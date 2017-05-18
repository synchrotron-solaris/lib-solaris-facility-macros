import sys
import time
import datetime
import numpy
import traceback

import PyTango
import sardana.macroserver.scan
import sardana.taurus.core.tango.sardana.pool
from sardana.macroserver.macro import macro
from sardana.macroserver.msexception import UnknownEnv


# Utilities --------------------------------------------------------------------


class HistoryError(Exception):
	pass


def calculatePic(data, det):
	# pic_data = {}
	motors = {}
	detv = []
	for i, dp in data.iteritems():
		for k, v in dp.data.iteritems():
			if k in ("point_nb", "timestamp"):
				continue

			dev = PyTango.DeviceProxy(k)
			if dev.info().dev_class == "Motor":
				if k not in motors:
					motors[k] = [v]
				else:
					motors[k].append(v)
			elif dev.alias().lower() == det.lower():
				detv.append(v)

	if not motors:
		return {}

	pic_data = {}
	for mot, mv in motors.iteritems():
		pic_data[mot] = mv[detv.index(max(detv))]
	return pic_data


def _center(x, y):
	xarr = numpy.ndarray(shape=(len(x),), buffer=numpy.array(x), dtype=float)
	yarr = numpy.ndarray(shape=(len(y),), buffer=numpy.array(y), dtype=float)

	num = numpy.sum(xarr * yarr)
	denom = numpy.sum(yarr).astype(numpy.float)
	try:
		result = num / denom
	except ZeroDivisionError:
		result = 0
	return result


def calculateCen(data, det):
	motors = {}
	detv = []
	for i, dp in data.iteritems():
		for k, v in dp.data.iteritems():
			if k in ("point_nb", "timestamp"):
				continue

			dev = PyTango.DeviceProxy(k)
			if dev.info().dev_class == "Motor":
				if k not in motors:
					motors[k] = [v]
				else:
					motors[k].append(v)
			elif dev.alias().lower() == det.lower():
				detv.append(v)

	if not motors:
		return {}

	cen_data = {}
	for mot, mv in motors.iteritems():
		cen_data[mot] = _center(mv, detv)
	return cen_data


def getDataFromLastScan(macro):
	try:
		hist = macro.getEnv("ScanHistory")
		if not hist:
			raise HistoryError("No scans in history.")
		data = hist[-1]["data"]
		if not data:
			raise HistoryError("No data in the last scan.")
	except HistoryError as e:
		macro.output(str(e))
		return None
	except:
		macro.output("No ScanHistory env or an error occured.")
		return None
	else:
		return data


def getFirstActiveDetector(macro):
	try:
		detector = macro.getEnv("ActiveDetectors")[0]
		if not detector:
			raise Exception()
	except:
		macro.output("No active detectors defined.")
		return None
	else:
		return detector.lower()


def moveToDetectorPosition(macro, data_id):
	data = getDataFromLastScan(macro)
	if not data:
		return

	det = getFirstActiveDetector(macro)
	if not det:
		return

	macro.output("First active detector: %s" % det)

	if data_id == "cen":
		macro.output("--> Calculating cen...")
		calc_values = calculateCen(data, det)
	if data_id == "pic":
		macro.output("--> Calculating pic...")
		calc_values = calculatePic(data, det)
	macro.output("--> Done.")

	for mot, pos in calc_values.iteritems():
		macro.output("Moving motor %s to position %s." % (mot, pos))
		macro.mv(mot, pos)


# GScan monkey patch -----------------------------------------------------------


def mpend(self):
	""" Monkey-patched GScan.end method that saves data for pic and cen macros """
	env = self._env
	env['endts'] = end_ts = time.time()
	env['endtime'] = datetime.datetime.fromtimestamp(end_ts)
	total_time = end_ts - env['startts']
	acq_time = env['acqtime']
	# env['deadtime'] = 100.0 * (total_time - estimated) / total_time

	env['deadtime'] = total_time - acq_time
	if 'delaytime' in env:
		env['motiontime'] = total_time - acq_time - env['delaytime']
	elif 'motiontime' in env:
		env['delaytime'] = total_time - acq_time - env['motiontime']

	self.data.end()
	try:
		scan_history = self.macro.getEnv('ScanHistory')
	except UnknownEnv:
		scan_history = []

	scan_file = env['ScanFile']
	if isinstance(scan_file, (str, unicode)):
		scan_file = scan_file,

	names = [col.name for col in env['datadesc']]

	history = dict(startts=env['startts'], endts=env['endts'],
				   estimatedtime=env['estimatedtime'],
				   deadtime=env['deadtime'], title=env['title'],
				   serialno=env['serialno'], user=env['user'],
				   ScanFile=scan_file, ScanDir=env['ScanDir'],
				   channels=names, data=self.data)
	scan_history.append(history)
	while len(scan_history) > self.MAX_SCAN_HISTORY:
		scan_history.pop(0)
	self.macro.setEnv('ScanHistory', scan_history)


# monkey-patch GScan's end method
sardana.macroserver.scan.GScan.end = mpend


# print info in dNscan
def mpdo_restore(self):
	# original do_restore
	try:
		if hasattr(self.macro, 'do_restore'):
			self.macro.do_restore()
	except:
		self.macro.warning("Failed to execute macro 'do_restore'")
		self.debug("Details:", exc_info=1)
	# END original do_restore
	else:
		# workaround for isinstance and issubclass not working when importing classes in different modules
		if "dNscan" in [c.__name__ for c in self.macro.__class__.__bases__]:
			self.macro.info("Reached start positions.")


# monkey-patch do_restore method
sardana.macroserver.scan.GScan.do_restore = mpdo_restore


def _information(self, tab='    '):
	indent = "\n" + tab + 10 * ' '
	msg = [self.getName() + ":"]
	try:
		state = str(self.state()).capitalize()
	except PyTango.DevFailed, df:
		if len(df.args):
			state = df.args[0].desc
		else:
			e_info = sys.exc_info()[:2]
			state = traceback.format_exception_only(*e_info)
	except:
		e_info = sys.exc_info()[:2]
		state = traceback.format_exception_only(*e_info)
	msg.append(tab + "   State: " + str(state))

	try:
		e_info = sys.exc_info()[:2]
		status = self.status()
		status = status.replace('\n', indent)
	except PyTango.DevFailed, df:
		if len(df.args):
			status = df.args[0].desc
		else:
			e_info = sys.exc_info()[:2]
			status = traceback.format_exception_only(*e_info)
	except:
		e_info = sys.exc_info()[:2]
		status = traceback.format_exception_only(*e_info)
	msg.append(tab + "  Status: " + str(status))

	return msg


sardana.taurus.core.tango.sardana.pool.PoolElement._information = _information


# Macros -----------------------------------------------------------------------


@macro()
def pic(self):
	""" Move motors from last scan to maximum value of first active detector. """
	moveToDetectorPosition(self, "pic")


@macro()
def cen(self):
	""" Move motors from last scan to mass center of first active detector. """
	moveToDetectorPosition(self, "cen")
