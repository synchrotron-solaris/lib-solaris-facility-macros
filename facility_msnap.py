from sardana.macroserver.macro import Macro, Type
import os



class msnap(Macro):
    """Creates snapshot of positions of all motors"""
    param_def = [
        ['comment', Type.String, None,
         'Comment for snapshot']
    ]

    def __init__(self, *args, **kwargs):
        Macro.__init__(self, *args, **kwargs)

    def run(self, *pars):
        try:
            snapDir = self.getEnv('SnapDir')
        except:
            self.error(
                "Aborting - undefined SnapDir (motor snapshot directory) environment variable")
            self.error(
                "Use senv to define it. Example: \"senv SnapDir /home/user/snapshots/\"")
            self.abort()

        if not snapDir.endswith("/"):
            snapDir += "/"

        try:
            snapID = self.getEnv('SnapID')
        except:
            self.setEnv('SnapID', 0)
            snapID = 0
        snapID = snapID + 1

        name = snapDir + pars[0] + ".txt" # do zrobienia

        with open(name, "r") as inputFile:
            self.setEnv('SnapID', snapID)
            self.info("Start of snapshot " + str(snapID))
            motors = self.findObjs("", type=Type.Moveable, subtype="Motor")
            for motor in motors:
                # test = motors[motor].name
                print motor


        #     for lineIn in inputFile:
        #         line = lineIn.strip()
        #         line = line.lower()
        #         if line.startswith("#"):  # ignore comments
        #             continue
        #         if line == "":  # ignore empty lines
        #             continue
        #         try:
        #             m, _ = self.createMacro(line)
        #         except Exception as e:
        #             self.error(
        #                 "Following exception occured when preparing macro %s:\n%s" % (
        #                 line, e))
        #             break
        #         self.output("--> Running macro: %s\n" % line)
        #         self.current = m
        #         self.runMacro(m)
        #         self.current = None
        # self.info("End of umacro " + pars[0])


class delmsnap(Macro):
    """Deletes previously created snapshot"""



class lsmsnap(Macro):
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
