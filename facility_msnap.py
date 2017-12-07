from sardana.macroserver.macro import Macro, Type, ParamRepeat
import os
from datetime import datetime
import re
from math import isnan
from math import isinf


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
        self.all_names = []

    def find_last_ID(self):
        file_list = sorted(os.listdir(self.snapDir))
        if len(file_list) == 0:
            return 0
        else:
            return int(file_list[-1].split('_')[0])

    def run(self, coms):
        try:
            check_snapdir(self)
        except:
            return

        snapID = self.find_last_ID()
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
            self.info("Start of snapshot " + str(snapID))
            motors = self.findObjs(".*", type_class=Type.Moveable,
                                   subtype="Motor")
            for motor in motors:
                name = str(motor.getName())
                matchObj = re.match(r"ES[UDRL]", name)
                if matchObj:
                    offset = str(motor.getOffset())
                    outputFile.write(name + " " + offset + "\n")
                    continue
                position = str(motor.getPosition())
                offset = str(motor.getOffset())
                outputFile.write(name + " " + position + " " + offset + "\n")
                self.output("Motor " + name + " saved")
            pseudomotors = self.findObjs("E[HV][OG]", type_class=Type.Moveable, # ESU, ESD, ESR, ESL, EHO, EHG, EVO, EVG
                                       subtype="Pseudomotor")
            # self.info(pseudomotors)
            for pseudomotor in pseudomotors:
                name = str(pseudomotor.getName())

                position = str(pseudomotor.getPosition())
                outputFile.write(name + " " + position + "\n")
                self.output("Pseudomotor " + name + " saved")
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
            else:
                str_snap_nr = str(snap_number)
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
        file_list = sorted(os.listdir(self.snapDir))
        if len(file_list) == 0:
            self.info('There are no motors snapshots saved')
            return
        self.output('ID\tTIMESTAMP\t\tCOMMENT')
        for file in file_list:
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
        else:
            str_snap_nr = str(snap_nr)
        for snap_file in sorted(os.listdir(self.snapDir)):
            if snap_file.startswith(str_snap_nr):
                with open(self.snapDir + snap_file, "r") as inputFile:
                    self.command = str()
                    self.counter = 0
                    for line in inputFile:
                        data = line.strip("\n").split(" ")
                        if len(data) == 3:
                            self.restore_motor(data[0], data[1], data[2])
                        else:
                            self.restore_pseudomotor(data[0], data[1])
                    if self.counter > 0:
                        self.execMacro("umv " + self.command)
                    else:
                        self.info('There are no motors to move')
                    break
        else:
            self.error("There's no such snapshot")
            return

    def restore_motor(self, name, position, offset):
        if position != 'None' and offset != 'None':
            motor = self.getMotor(name)
            if float(offset) != motor.getOffset():
                motor.setOffset(offset)
                po = motor.getDialPositionObj()
                upper_dial = float(po.getMaxValue())
                lower_dial = float(po.getMinValue())
                upper = upper_dial + float(offset)
                lower = lower_dial + float(offset)
                self.execMacro("set_lim", motor, lower, upper)
            if float(position) != motor.getPosition():
                self.command += name + " " + position + " "
                self.counter += 1

    def restore_pseudomotor(self, name, data):
        if data != 'None':
            matchObj = re.match(r"ES[UDRL]", name)
            if matchObj:
                motor = self.getMotor(name)
                if float(data) != motor.getOffset():
                    motor.setOffset(data)
            matchObj = re.match(r"E[HV][OG]", name)
            if matchObj:
                pseudomotor = self.getPseudoMotor(name)
                if float(data) != pseudomotor.getPosition():
                    self.command += name + " " + data + " "
                    self.counter += 1
