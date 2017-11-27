from sardana.macroserver.macro import Macro, Type, ParamRepeat
import os
from datetime import datetime


def check_snapdir(context):
    """checks if SnapDir variable is set properly"""
    try:
        context.snapDir = context.getEnv('SnapDir')
    except:
        context.error(
            "Aborting - undefined SnapDir (motor snapshot directory) environment variable")
        context.error(
            "Use senv to define it. Example: \"senv SnapDir /home/user/snapshots/\"")
        raise Exception('Bad SnapDir')

    if not context.snapDir.endswith("/"):
        context.snapDir += "/"


class msnap(Macro):
    """Creates snapshot of positions of all motors"""
    param_def = [
        ['comment_list',
         ParamRepeat(['comment', Type.String, None, 'Comment for snapshot']),
         None, 'Comment for snapshot']
    ]

    snapDir = ''

    def __init__(self, *args, **kwargs):
        Macro.__init__(self, *args, **kwargs)

    def run(self, coms):
        try:
            check_snapdir(self)
        except:
            return
        try:
            snapID = self.getEnv('SnapID')
        except:
            self.setEnv('SnapID', 0)
            snapID = 0
        try:
            last_snap = int(sorted(os.listdir(self.snapDir))[-1].split("_")[0])
            if snapID < last_snap:
                snapID = last_snap
                self.setEnv('SnapID', last_snap)
        except:
            pass
        snapID = snapID + 1

        timestamp = str(datetime.now())
        timestamp = timestamp.split(".")[0]

        if snapID < 10:
            str_snapID = "00" + str(snapID)
        elif snapID < 100:
            str_snapID = "0" + str(snapID)
        else:
            str_snapID = str(snapID)

        name = str_snapID + "_" + timestamp + "_" + " ".join(coms) + ".txt"
        with open(self.snapDir + name, "w") as outputFile:
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
        ['snap_number',
         ParamRepeat(['number', Type.Integer, None, 'Numbers of snapshots to delete']),
         None, 'Number of snapshot to delete']
    ]

    snapDir = ''

    def run(self, snap_numbers):
        snap_numbers = list(set(snap_numbers))  # deleting duplicates
        try:
            check_snapdir(self)
        except:
            return
        for snap_number in snap_numbers:
            if len(str(snap_number)) == 1:
                str_snap_nr = "00" + str(snap_number)
            elif len(str(snap_number)) == 2:
                str_snap_nr = "0" + str(snap_number)
            for snap_file in sorted(os.listdir(self.snapDir)):
                if snap_file.startswith(str_snap_nr):
                    os.remove(self.snapDir + str(snap_file))
                    self.info("Snapshot " + str(snap_number) + " deleted")
                    break
            else:
                self.error("There's no snapshot " + str(snap_number))


class lssnap(Macro):
    """List of created snapshots stored in txt files"""

    snapDir = ''

    def run(self):
        try:
            check_snapdir(self)
        except:
            return
        self.output('ID\tTIMESTAMP\t\tCOMMENT')
        for file in sorted(os.listdir(self.snapDir)):
            if file.endswith(".txt"):
                line = file.split(".")[0]
                self.output(line.replace('_', '\t'))

class umvsnap(Macro):
    """Restore motors positions from snapshot"""
    param_def = [
        ['snap_nr', Type.Integer, None, 'Number of snapshot to restore']
    ]

    snapDir = ''

    def run(self, snap_nr):
        try:
            check_snapdir(self)
        except:
            return
        if len(str(snap_nr)) == 1:
            str_snap_nr = "00" + str(snap_nr)
        elif len(str(snap_nr)) == 2:
            str_snap_nr = "0" + str(snap_nr)
        for snap_file in sorted(os.listdir(self.snapDir)):
            if snap_file.startswith(str_snap_nr):
                with open(self.snapDir + snap_file, "r") as inputFile:
                    command = str()
                    for line in inputFile:
                        name, position = line.strip("\n").split(" ")
                        if position != 'None':
                            command += name + " " + position + " "
                    command = "umv " + command
                    self.execMacro(command)
                    break
        else:
            self.error("There's no such snapshot")
            return
