from sardana.macroserver.macro import Macro, Type
from sardana.macroserver.scan import SScan


class timescan(Macro):
	hints = {"scan": "timescan"}
	env = ("ActiveMntGrp",)
	param_def = [
		["integ_time", Type.Float, 1, "Integration time"]
	]

	def prepare(self, integ_time, **opts):
		self.stopped = False
		self.integ_time = integ_time

		self.interv_size = 1

		# TM01 motor must be defined as simulation motor with accel and decel times as small as possible
		# It should not have any limits configured on position
		# Velocity for this motor should be around 100 for proper operation
		motor = self.getObj("TM01")
		self.start = motor.Position

		self._gScan = SScan(self, generator=self._generator, moveables=[motor])

	def _generator(self):
		step = {}
		step["integ_time"] = self.integ_time
		self.point_no = 0
		while not self.stopped:
			step["positions"] = [self.start + self.point_no * self.interv_size]
			step["point_id"] = self.point_no
			self.point_no = self.point_no + 1
			yield step

	def on_abort(self):
		self._gScan.end()
		self.stopped = True

	def run(self, *args):
		for step in self._gScan.step_scan():
			if not self.stopped:
				yield step

	@property
	def data(self):
		return self._gScan.data


class timescanf(Macro):
	pass
