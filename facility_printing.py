import os
import re
import time
import PyTango
from threading import Thread
from tempfile import NamedTemporaryFile
from sardana.macroserver.macro import macro, Type


# Utilities --------------------------------------------------------------------


def DoorCaptureThread(doorName, macro, cpi, lpi):
	shared_path = "/mnt/control/print/"
	door = PyTango.DeviceProxy(doorName)
	tmp = NamedTemporaryFile(prefix="spockprint", delete=False)
	param_fn = "cfg_%s" % os.path.basename(tmp.name)
	tmp.write(":from %s\n" % doorName)

	with open("%s" % os.path.join(shared_path, param_fn), "w") as param_f:
		param_f.write("-o cpi=%d -o lpi=%d" % (cpi, lpi))

	def door_event(ev):
		state = ev.attr_value.value
		if state == PyTango.DevState.ON or state == PyTango.DevState.ALARM:
			if door.Output:
				tmp.write("\n".join(door.Output))
		if state == PyTango.DevState.RUNNING:
			try:
				command = re.search(r"\[START\] runMacro Macro '(.*) -> .*'", "\n".join(door.Debug)).group(1)
			except:
				command = "/could not get macro name/"		# sometimes macro execution is faster than event, can't do much about it
			if command.startswith("echo"):
				msg = None
				while msg is None:			# I get event faster than macro can set env variable
					try:					# therefore I need to wait for it
						msg = macro.getEnv("PrintoutMessage")
					except:
						pass
				tmp.write("\n\n========== %s ==========" % msg)
				macro.unsetEnv("PrintoutMessage")
				return
			tmp.write("\n\n--> %s\n" % command)

	ev = door.subscribe_event("State", PyTango.EventType.CHANGE_EVENT, door_event)
	while macro.getEnv("CaptureActive"):
		pass
	door.unsubscribe_event(ev)
	tmp.close()
	os.system("cp %s %s" % (tmp.name, shared_path))		# copy capture file to shared path
	# os.system("lpr -r %s" % tmp.name)		# lpr -r removes source file after printing


# Macros -----------------------------------------------------------------------


@macro([["cpi", Type.Integer, 15, "Characters per inch"], ["lpi", Type.Integer, 9, "Lines per inch"]])
def pon(self, cpi, lpi):
	""" Start capturing door operations to file, so it can be later printed using "poff". """
	try:
		if self.getEnv("CaptureActive"):
			self.output("Door capture is already active.\nNot starting again.")
			return
	except:
		pass
	thr = Thread(target=DoorCaptureThread, args=(self.getDoorName(), self, cpi, lpi))
	self.setEnv("CaptureActive", True)
	thr.start()
	self.output("Door capture thread started at %s." % time.asctime())


@macro()
def poff(self):
	""" Stop capturing and print what was captured. """
	try:
		if not self.getEnv("CaptureActive"):
			self.output("Door capture is not started.")
			return
	except:
		pass
	self.setEnv("CaptureActive", False)
	self.output("Door capture thread stopped at %s." % time.asctime())


@macro([['msg', [['m', Type.String, None, 'Single word of the message']], None, 'Message']])
def echo(self, *msg):
	""" Add custom message to printout, valid only if door capture is active.
		If the message is "time", then the current time is added instead. """
	try:
		if not self.getEnv("CaptureActive"):
			self.output("Door capture is not started. Not doing anything.")
			return
	except:
		pass
	msg = msg[0]		# Sardana 2 compability
	msg = " ".join(msg)
	if msg == "time":
		msg = time.asctime()
	self.setEnv("PrintoutMessage", msg)
