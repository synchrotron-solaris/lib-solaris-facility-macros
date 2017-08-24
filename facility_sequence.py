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

class useq(Macro):
	"""Run a sequence of macros (spock style) saved in txt file"""

	param_def = [
		['sequence_name',   Type.String,   None, 'Name of file (without extention) includes user sequence']
	]

	def run(self, *pars):
		self.output("Running macro useq " + pars[0])
		try:
			useq_dir = self.getEnv('UseqDir')
		except:
			self.error("Aborting - undefined UseqDir (user sequences directory) environment variable")
			self.error("Use senv macro to define it. Example: \"senv UseqDir /home/user/sequences/\"")
			self.error("Remember about slash at the end of directory path")
			self.abort()
		name = useq_dir + pars[0] + ".txt"
		self.output("User macro file name: " + name)
		nr = 0
		error = 0
		with open(name, "r") as inputFile:
			for lineIn in inputFile:
				macro = lineIn.rstrip()
				nr += 1
				if macro == "":
					continue
				try:
					self.prepareMacro(macro)
				except Exception as e:
					error = 1
					self.error("Error in line " + str(nr) + " -> " + lineIn.rstrip())
					self.error(e.message)
		if error == 1:
			self.abort()
		with open(name, "r") as inputFile:
			for lineIn in inputFile:
				macro = lineIn.rstrip()
				if macro == "":
					continue
				self.output("Executing --> " + lineIn.rstrip())
				self.execMacro(macro)
		self.output("End of macro useq " + pars[0])

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
