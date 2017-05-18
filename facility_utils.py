import time
from math import isnan, isinf
from sardana.macroserver.macro import macro, Macro, Type


@macro([["t", Type.Float, None, "Time in seconds"]])
def sleep(self, t):
	""" Waits for given time """
	time.sleep(t)


class setaxis(Macro):
	"""Sets the USER position and limit switches of the motor to the specified value (by changing OFFSET and keeping DIAL)"""

	param_def = [
		['motor', Type.Motor, None, 'Motor name'],
		['pos', Type.Float, None, 'Position to move to']
	]

	def run(self, motor, pos):
		name = motor.getName()
		old_pos = motor.getPosition(force=True)
		offset_attr = motor.getAttribute('Offset')
		old_offset = offset_attr.read().value
		new_offset = pos - (old_pos - old_offset)
		offset_attr.write(new_offset)

		# Set user limit switches
		po = motor.getPositionObj()
		upper = float(po.getMaxValue())
		lower = float(po.getMinValue())
		if not (isnan(upper) or isinf(upper)):
			upper = upper - old_offset + new_offset
		if not (isnan(lower) or isinf(lower)):
			lower = lower - old_offset + new_offset
		self.execMacro("set_lim", motor, lower, upper)

		self.output("%s reset from %.4f (offset %.4f) to %.4f (offset %.4f)" % (name, old_pos, old_offset, pos, new_offset))


@macro()
def scanhistory(self):
	""" Shows scan history exactly as it is represented inside Sardana
		(mostly for debugging purposes) """
	try:
		hist = self.getEnv("ScanHistory")
	except:
		self.output("No scan history.")
		return

	for scan in hist:
		self.output("---------------------------")
		for k, v in scan.iteritems():
			self.output("   %s: %s" % (k, v))
	self.output(">END")


@macro([["group", Type.String, None, "Measurement group name"]])
def amg(self, group):
	""" Shortcut to 'senv ActiveMntGrp' """
	self.execMacro("senv ActiveMntGrp %s" % group)
