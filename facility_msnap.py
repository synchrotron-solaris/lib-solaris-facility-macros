from sardana.macroserver.macro import Macro, Type, ParamRepeat
import os
from datetime import datetime


class msnap(Macro):
    """Creates snapshot of positions of all motors"""
    param_def = [
        ['comment_list',
         ParamRepeat(['comment', Type.String, None, 'something']),
         None, 'Comment for snapshot']
    ]

    def __init__(self, *args, **kwargs):
        Macro.__init__(self, *args, **kwargs)

    def run(self, coms):
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

        timestamp = str(datetime.now())
        timestamp = timestamp.split(".")[0]
        name = str(snapID) + "_" + timestamp + "_" + " ".join(coms) + ".txt"
        with open(snapDir + name, "w") as outputFile:
            self.setEnv('SnapID', snapID)
            self.info("Start of snapshot " + str(snapID))
            motors = self.findObjs(".*", type_class=Type.Moveable, subtype="Motor")
            for motor in motors:
                # self.info(str(motor))
                name = str(motor.getName())
                position = str(motor.getPosition())
                outputFile.write(name + " " + position + "\n")
            self.info("End of snapshot " + str(snapID))


class delsnap(Macro):
    """Deletes previously created snapshot"""
    param_def = [
        ['snap_nr', Type.Integer, None, 'Number of snapshot to delete']
    ]

    def run(self, snap_nr):
        try:
            snapDir = self.getEnv('SnapDir')
        except:
            self.error("Aborting - undefined SnapDir (motor snapshot directory) environment variable")
            self.error("Use senv to define it. Example: \"senv SnapDir /home/user/snapshots/\"")
            self.abort()
        if not snapDir.endswith("/"):
            snapDir += "/"
        for snap_file in sorted(os.listdir(snapDir)):
            if snap_file.startswith(str(snap_nr)):
                os.remove(snapDir + str(snap_file))
                self.info("Snapshot deleted")
                break
        else:
            self.error("There's no such snapshot")
            return


class lssnap(Macro):
    """List of created snapshots stored in txt files"""
    def run(self):
        try:
            snapDir = self.getEnv('SnapDir')
        except:
            self.error("Aborting - undefined SnapDir (motor snapshot directory) environment variable")
            self.error("Use senv to define it. Example: \"senv SnapDir /home/user/snapshots/\"")
            self.abort()
        self.info("List of snapshots from directory " + snapDir)
        if not snapDir.endswith("/"):
            snapDir += "/"
        for file in sorted(os.listdir(snapDir)):
            if file.endswith(".txt"):
                self.output(file.split(".")[0])


class umvsnap(Macro):
    """Restore motors positions from snapshot"""
    param_def = [
        ['snap_nr', Type.Integer, None, 'Number of snapshot to restore']
    ]

    def run(self, snap_nr):
        try:
            snapDir = self.getEnv('SnapDir')
        except:
            self.error("Aborting - undefined SnapDir (motor snapshot directory) environment variable")
            self.error("Use senv to define it. Example: \"senv SnapDir /home/user/snapshots/\"")
            self.abort()
        if not snapDir.endswith("/"):
            snapDir += "/"
        for snap_file in sorted(os.listdir(snapDir)):
            if snap_file.startswith(str(snap_nr)):
                with open(snapDir + snap_file, "r") as inputFile:
                    command = str()
                    for line in inputFile:
                        name, position = line.strip("\n").split(" ")
                        command += name + " " + position + " "
                    command = "umv " + command
                    self.execMacro(command)
                    break
        else:
            self.error("There's no such snapshot")
            return
