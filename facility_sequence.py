from sardana.macroserver.macro import Macro, Type
import os


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

class umacro(Macro):
    """Run a sequence of macros (spock style) saved in txt file"""

    param_def = [
        ['sequence_name',   Type.String,   None, 'Name of file (without extention) includes user macro']
    ]

    def __init__(self, *args, **kwargs):
        Macro.__init__(self, *args, **kwargs)
        self.current = None

    def run(self, *pars):
        try:
            macroDir = self.getEnv('MacroDir')
        except:
            self.error("Aborting - undefined MacroDir (user macro directory) environment variable")
            self.error("Use senv to define it. Example: \"senv MacroDir /home/user/sequences/\"")
            self.abort()
        if not macroDir.endswith("/"):
            macroDir += "/"
        name = macroDir + pars[0] + ".txt"
        with open(name, "r") as inputFile:
            self.info("Start of umacro " + pars[0])
            for lineIn in inputFile:
                line = lineIn.strip()
                line = line.lower()
                if line.startswith("#"):  # ignore comments
                    continue
                if line == "":  # ignore empty lines
                    continue
                try:
                    m, _ = self.createMacro(line)
                except Exception as e:
                    self.error("Following exception occured when preparing macro %s:\n%s" % (line, e))
                    break
                self.output("--> Running macro: %s\n" % line)
                self.current = m
                self.runMacro(m)
                self.current = None
        self.info("End of umacro " + pars[0])

    def on_abort(self):
        if self.current:
            self.current.stop()

class prudef(Macro):
	"""Print user macro content"""

	param_def = [
		['macro_name',   Type.String,   None, 'Name of file (without extention) includes user macro']
	]

	#    env = ('MacroDir')

	def run(self, *pars):

		try:
			macroDir = self.getEnv('MacroDir')
		except:
			self.error("Aborting - undefined MacroDir (user macro directory) environment variable")
			self.error("Use senv to define it. Example: \"senv MacroDir /home/user/sequences/\"")
			self.abort()
		if not macroDir.endswith("/"):
			macroDir += "/"
		name = macroDir + pars[0] + ".txt"
		nr = 0
		error = 0
		macrolist = []
		with open(name, "r") as inputFile:
			for lineIn in inputFile:
				self.output(lineIn.strip())

class lsumacro(Macro):
	"""List of user defined sequences stored in txt files"""
	def run(self):
		try:
			macroDir = self.getEnv('MacroDir')
		except:
			self.error("Aborting - undefined MacroDir (user macro directory) environment variable")
			self.error("Use senv to define it. Example: \"senv MacroDir /home/user/sequences/\"")
			self.abort()
		self.info("List of user macros from directory " + macroDir)
		if not macroDir.endswith("/"):
			macroDir += "/"
		for file in sorted(os.listdir(macroDir)):
			if file.endswith(".txt"):
				self.output(file.split(".")[0])

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
