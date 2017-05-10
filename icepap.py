# !IMPORTANT! solaris_sardana_utils depends on old repos and build method

from sardana.macroserver.macro import Macro, Type
from solaris_sardana_utils.icepap import create_motor_info_dict, home, home_group, home_strict, home_group_strict


class ipap_homing(Macro):
    """This macro will execute an icepap homing routine for all motors passed as arguments in directions passes as arguments.
       Directions are considered in pool sense.
       Icepap homing routine is parametrizable in group and strict sense, so it has 4 possible configurations.
       Macro result depends on the configuration which you have chosen:
       - HOME (macro result is True if all the motors finds home, otherwise result is False)
       - HOME GROUP (macro result is True if all the motors finds home, otherwise result is False)
       - HOME STRICT (macro result is True when first motor finds home, otherwise result is False)
       - HOME GROUP STRICT (macro result is True when first motor finds home, otherwise result is False)
    """

    param_def = [
        ["group", Type.Boolean, False, "If performed group homing."],
        ["strict", Type.Boolean, False, "If performed strict homing."],
        ['motor_direction_list',
            [
                ['motor', Type.Motor, None, 'Motor to be homed.'],
                ['direction', Type.Integer, None, 'Direction of homing (in pool sense) <-1|1>']
            ],
            None, 'List of motors and homing directions.'
        ]
    ]

    result_def = [
        ['homed', Type.Boolean, None, 'Motors homed state']
    ]

    def prepare(self, *args, **opts):
        self.group = args[0]
        self.strict = args[1]
        self.motors = []

        motors_directions = args[2:]
        self.motorsInfoList = [create_motor_info_dict(m, d) for m, d in motors_directions[0]]       # Sardana 2 compability

        # getting motion object for automatic aborting
        motorNames = [motorInfoDict['motor'].name for motorInfoDict in self.motorsInfoList]
        self.getMotion(motorNames)

    def run(self, *args, **opts):
        if self.group and self.strict:
            return home_group_strict(self, self.motorsInfoList)
        elif self.group:
            return home_group(self, self.motorsInfoList)
        elif self.strict:
            return home_strict(self, self.motorsInfoList)
        else:
            return home(self, self.motorsInfoList)
