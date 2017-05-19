from sardana.macroserver.macro import macro, Type


@macro([['detectors', [['det', Type.String, None, 'detector']], None, 'List of detectors']])
def plotselect(self, *detectors):
	""" Set list of active detectors for live plotting and pic/cen macros """
	detectors = detectors[0]		# Sardana 2 compability
	if detectors:
		valid_dets = [det.name.lower() for det in self.getObjs(".*", type_class=Type.ExpChannel)]
		for det in detectors:
			if det.lower() not in valid_dets:
				self.output("Detector %s is not valid (probably doesn't exist).\nNot selecting anything." % det)
				return
		self.setEnv("ActiveDetectors", detectors)
	else:
		detectors = self.getEnv("ActiveDetectors")
	self.output("ActiveDetectors = %s" % (detectors,))


@macro()
def getactivedetectors(self):
	""" Returns a list of active detectors """
	try:
		dets = self.getEnv("ActiveDetectors")
	except:
		self.output("No active detectors.")
	else:
		self.output(dets)
