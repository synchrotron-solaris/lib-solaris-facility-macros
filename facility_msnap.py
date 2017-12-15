from sardana.macroserver.macro import Macro, Type, ParamRepeat
import os
from datetime import datetime
import re
from tango import DeviceProxy


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
            outputFile.write("#NAME\tDIAL_POSITION\tPOSITION\tSIGN\tOFFSET\n")
            motors = self.findObjs(".*", type_class=Type.Moveable,
                                   subtype="Motor")
            for motor in motors:
                name = str(motor.getName())
                dial_position = str(motor.getDialPosition())
                position = str(motor.getPosition())
                sign = str(motor.getSign())
                offset = str(motor.getOffset())
                outputFile.write(name + "\t" + dial_position + "\t" + position + "\t" + sign + "\t" + offset + "\n")
                self.output("Motor " + name + " saved")
            pseudomotors = self.findObjs(r"E[HV][OG]", type_class=Type.Moveable, subtype="Pseudomotor")
            for pseudomotor in pseudomotors:
                name = str(pseudomotor.getName())
                position = str(pseudomotor.getPosition())
                outputFile.write(name + "\t" + position + "\n")
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

    def __init__(self, *args, **kwargs):
        Macro.__init__(self, *args, **kwargs)
        self.command = str()
        self.counter = 0
        self.dial_motors = {}

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
                    for line in inputFile:
                        if line.startswith("#"):
                            continue
                        data = line.strip("\n").split("\t")
                        if len(data) == 5:
                            self.restore_motor(data[0], data[1], data[2], data[3], data[4])
                        else:
                            self.restore_pseudomotor(data[0], data[1])
                if self.counter > 0:
                    self.execMacro("umv " + self.command)
                    for name in self.dial_motors:
                        motor = self.getMotor(name)
                        dial_position = self.dial_motors[name]
                        if motor.getDialPosition() != float(dial_position):
                            self.error("Motor " + name + " is not OK")
                        else:
                            self.info("Motor " + name + " is OK")
                else:
                    self.info('There are no motors to restore')
                break
        else:
            self.error("There's no such snapshot")
            return

    def restore_motor(self, name, dial_position, position, sign, offset):
        if all([name, dial_position, position, sign, offset]):
            motor = self.getMotor(name)
            matchObj = re.match(r"ES[UDRL]", name)
            if matchObj:
                if float(offset) != motor.getOffset():
                    motor.setOffset(offset)
                    return
            if int(sign) != motor.getSign():
                # motor.getAttrEG('sign').write(int(sign))  # there's no 'getSignObj' method
                motor_dp = DeviceProxy(name)
                motor_dp.Sign = int(sign)

                po = motor.getPositionObj()
                lower = -float(po.getMaxValue())
                upper = -float(po.getMinValue())
                command = name + " " + str(lower) + " " + str(upper)
                self.output(command)
                try:
                    self.execMacro("set_lim " + command)
                except:
                    self.execMacro("set_lim " + command)
            if float(offset) != motor.getOffset():
                motor.setOffset(offset)
                po = motor.getDialPositionObj()
                upper_dial = float(po.getMaxValue())
                lower_dial = float(po.getMinValue())
                upper = upper_dial + float(offset)
                lower = lower_dial + float(offset)
                command = name + " " + str(lower) + " " + str(upper)
                self.output(command)
                try:
                    self.execMacro("set_lim " + command)
                except:
                    self.execMacro("set_lim " + command)
            if float(position) != motor.getPosition():
                self.command += name + " " + position + " "
                self.counter += 1
            self.dial_motors[name] = dial_position

    def restore_pseudomotor(self, name, position):
        if position != 'None':
            matchObj = re.match(r"E[HV][OG]", name)
            if matchObj:
                pseudomotor = self.getPseudoMotor(name)
                if float(position) != pseudomotor.getPosition():
                    self.command += name + " " + position + " "
                    self.counter += 1
