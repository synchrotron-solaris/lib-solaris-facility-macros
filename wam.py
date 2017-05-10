import datetime
from taurus.console.table import Table

import PyTango
from sardana.macroserver.macro import Macro, Type, ViewOption


class _wmm(Macro):
	"""Show motor positions"""

	param_def = [['motor_list', [['motor', Type.Moveable, None, 'Motor to move']], None, 'List of motor to show']]

	def run(self, *motor_list):
		show_dial = self.getViewOption(ViewOption.ShowDial)
		show_ctrlaxis = self.getViewOption(ViewOption.ShowCtrlAxis)
		pos_format = self.getViewOption(ViewOption.PosFormat)
		motor_width = 9
		motors = {}			# dict(motor name: motor obj)
		requests = {}		# dict(motor name: request id)
		data = {}			# dict(motor name: list of motor data)
		# sending asynchronous requests: neither Taurus nor Sardana extensions
		# allow asynchronous requests - use PyTango asynchronous request model
		motor_list = motor_list[0]      # Sardana 2 compability
		for motor in motor_list:
			name = motor.getName()
			motors[name] = motor
			args = ('position',)
			if show_dial:
				args += ('dialposition',)
			_id = motor.read_attributes_asynch(args)
			requests[name] = _id
			motor_width = max(motor_width, len(name))
			data[name] = []
		# get additional motor information (ctrl name & axis)
		if show_ctrlaxis:
			for name, motor in motors.iteritems():
				ctrl_name = self.getController(motor.controller).name
				axis_nb = str(getattr(motor, "axis"))
				data[name].extend((ctrl_name, axis_nb))
				motor_width = max(motor_width, len(ctrl_name), len(axis_nb))
		# collect asynchronous replies
		while len(requests) > 0:
			req2delete = []
			for name, _id in requests.iteritems():
				motor = motors[name]
				try:
					attrs = motor.read_attributes_reply(_id)
					for attr in attrs:
						value = attr.value
						if value is None:
							value = float('NaN')
						data[name].append(value)
					req2delete.append(name)
				except PyTango.AsynReplyNotArrived:
					continue
				except PyTango.DevFailed:
					data[name].append('NaN')
					if show_dial:
						data[name].append('NaN')
					req2delete.append(name)
					self.debug('Error when reading %s position(s)' % name)
					self.debug('Details:', exc_info=1)
					continue
			# removing motors which alredy replied
			for name in req2delete:
				requests.pop(name)
		# define format for numerical values
		fmt = '%c.%df' % ('%', motor_width - 5)
		if pos_format > -1:
			fmt = '%c.%df' % ('%', int(pos_format))
		# prepare row headers and formats
		row_headers = []
		t_format = []
		if show_ctrlaxis:
			row_headers += ['Ctrl', 'Axis']
			t_format += ['%*s', '%*s']
		row_headers.append('User')
		t_format.append('%*s')		# fmt)
		if show_dial:
			row_headers.append('Dial')
			t_format.append('%*s')		# fmt)
		# sort the data dict by keys
		col_headers = []
		values = []
		for mot_name, mot_values in sorted(data.items()):
			col_headers.append([mot_name])		# convert name to list
			values.append(mot_values)

		# CODE FROM lib-solaris-motorlistmacro/WAco.py by Przemyslaw Sagalo
# ------------------------------------------------------------------------------

		# Key, which we use to sort
		# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
		key = [
			's1u', 's1d', 's1l', 's1r', 's1ho', 's1hg', 's1vo', 's1vg',
			's2u', 's2d', 's2l', 's2r', 's2ho', 's2hg', 's2vo', 's2vg',
			's3u', 's3d', 's3l', 's3r', 's3ho', 's3hg', 's3vo', 's3vg',
			'm1y', 'm1z', 'm1pitch', 'm1roll', 'm1yaw', 'bds1', 'bds2', 'bds3',
			'm2y', 'm2z', 'm2pitch', 'm2roll', 'm2yaw', 'm2exch', 'bds5', 'bds6',
			'm3y', 'm3z', 'm3pitch', 'm3roll', 'm3yaw', '', '', '',
			'plmy', 'plmpitch', 'gry', 'grpitch', 'energy', 'cff', '', '',
			'esu', 'esd', 'esl', 'esr', 'esho', 'eshg', 'esvo', 'esvg',
			'escham', 'tx', 'ty', 'tz'
		]
		# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

		# Part, where headers are sorted
		sort_col_headers = col_headers
		sort_col_headers.sort()
		sort_col_headers_set = []
		sort_col_headers_alph = []

		# Using the key
		for n in key:
			if n:
				for m in sort_col_headers:
					if m[0].lower() == n:		# .startswith(n):
						sort_col_headers_set.append(m[0])
			else:
				sort_col_headers_set.append(n)

		# Others, alphabetic
		for m in sort_col_headers:
			if (m[0] in sort_col_headers_set) == 0:
				sort_col_headers_alph.append(m[0])
		pattern = sort_col_headers_set + sort_col_headers_alph

		# The part, where proper sort have place.
		new_col_headers = []
		new_values = []

		for f in pattern:
			new_col_headers.append([f])
			if f:
				new_values.append([fmt % v for v in values[col_headers.index([f])]])		# % values[col_headers.index([f])][0], fmt % values[col_headers.index([f])][1] ])
			else:
				new_values.append(["", ""])

		col_headers = new_col_headers
		values = new_values
# ------------------------------------------------------------------------------

		# create and print table
		table = Table(values, elem_fmt=t_format, term_width=90,		# term_width value is set to ensure printing 8 motors in line
					  col_head_str=col_headers, col_head_width=motor_width,
					  row_head_str=row_headers)
		for line in table.genOutput():
			self.output(line)


class wam(Macro):
	"""Show all motor positions"""

	def prepare(self, **opts):
		self.all_motors = self.findObjs(".*", type_class=Type.Moveable)
		self.table_opts = {}

	def run(self):
		nr_motors = len(self.all_motors)
		if nr_motors == 0:
			self.output('No motor defined')
			return

		show_dial = self.getViewOption(ViewOption.ShowDial)
		if show_dial:
			self.output('Current positions (user, dial) on %s' % datetime.datetime.now().isoformat(' '))
		else:
			self.output('Current positions (user) on %s' % datetime.datetime.now().isoformat(' '))
		self.output('')
		self.execMacro('_wmm', self.all_motors, **self.table_opts)
