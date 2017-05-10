# !IMPORTANT! Not adapted for Sardana 2.x
# !IMPORTANT! solaris_sardana_utils depends on old repos and build method

from sardana.macroserver.macro import Macro, Type, ParamRepeat

from solaris_sardana_utils.homing import setup_motors_configuration, execute_homing_from_hardlimit
from solaris_sardana_utils.pseudomotors import get_physical_motors_list


class home_from_hardlimit(Macro):

    MAX_LIM_RETRY = 5

    param_def = [
        ["motor_list", ParamRepeat(['motor', Type.Motor, None, 'Motor to be homed.']), None, "List of motors to be homed"]
    ]

    result_def = [
        ["homed", Type.Boolean, False, "Is operation successful"]
    ]

    def prepare(self, *args, **kwargs):
        motor_list = args
        self.physical_motors = setup_motors_configuration(self, motor_list)

    def run(self, *args):
        res = execute_homing_from_hardlimit(self, self.physical_motors)
        return res


class home_pseudo(Macro):

    param_def = [
        ["pseudo_ctrl", Type.Controller, None, "PseudoMotor controller to be homed"]
    ]

    result_def = [
        ["homed", Type.Boolean, False, "Is operation successful"]
    ]

    def prepare(self, pseudo_ctrl):

        if pseudo_ctrl.getMainType() != 'PseudoMotor':
            self.error('%s requires a PseudoMotor controller' % self.getName())
            return
        self.info(type(pseudo_ctrl))
        physical_names = get_physical_motors_list(self, pseudo_ctrl)

        motor_list = []
        for motor_name in physical_names:
            motor_list.append(self.getMotor(motor_name))

        self.physical_motors = setup_motors_configuration(self, motor_list)

    def run(self, pseudo_ctrl):
        res = execute_homing_from_hardlimit(self, self.physical_motors)
        return res
