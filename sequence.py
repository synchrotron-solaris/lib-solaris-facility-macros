from sardana.macroserver.macro import Macro, Type


class seq(Macro):
	""" Run a sequence of macros """

	interactive = True
	param_def = [["macros", [["macro", Type.String, None, "Macro to execute"]], None, "List of macros to execute"]]

	def __init__(self, *args, **kwargs):
		Macro.__init__(self, *args, **kwargs)
		self.current = None

	def run(self, *macros):
		macros = macros[0]		# Sardana 2 compability
		for macro in macros:
			self.output("\n--> Preparing macro: %s" % macro)
			try:
				m, _ = self.createMacro(macro)
			except Exception as e:
				cont = self.input("Following exception occured when preparing macro %s:\n%s\n\nContinue (y/n)?" % (macro, e),
								  data_type=("y", "n"),
								  title="Continue?",
								  default_value="n"
				)
				if cont == "y":
					continue
				else:
					break

			self.output("--> Running macro: %s\n" % macro)
			self.current = m
			self.runMacro(m)
			self.current = None

	def on_abort(self):
		if self.current:
			self.current.stop()


class rep(Macro):
	""" Repeat executing macro """

	interactive = True
	param_def = [["count", Type.Integer, None, "Number of repetitions"], ["macro", Type.String, None, "Macro to execute"]]

	def __init__(self, *args, **kwargs):
		Macro.__init__(self, *args, **kwargs)
		self.current = None

	def run(self, count, macro):
		for i in range(1, count + 1):
			self.output("\n[%6d] --> Preparing macro: %s" % (i, macro))
			try:
				m, _ = self.createMacro(macro)
			except Exception as e:
				cont = self.input("[%6d] Following exception occured when preparing macro %s:\n%s\n\nContinue (y/n)?" % (i, macro, e),
								  data_type=("y", "n"),
								  title="Continue?",
								  default_value="n"
				)
				if cont == "y":
					continue
				else:
					break

			self.output("[%6d] --> Running macro: %s\n" % (i, macro))
			self.current = m
			self.runMacro(m)
			self.current = None

	def on_abort(self):
		if self.current:
			self.current.stop()
