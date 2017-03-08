from LeekLabber import *
from LLSimpleTasks import *
from LLMicrowaveTasks import *
import LeekLabber as LL

class LLTaskSingleQMeasure(LLTask):
    def __init__(self, parent=None):
        super(LLTaskSingleQMeasure, self).__init__(parent)
        self.p_qubit = None
        self.add_parameter('p_qubit', label="Qubit Device", ptype=LLObjectParameter.PTYPE_LLOBJECT, select_from=LL.LL_ROOT.devices)

        self.p_subtask = None
        self.add_parameter('p_subtask', label="subtask", ptype=LLObjectParameter.PTYPE_LLOBJECT, viewable=False, read_only=True)

    def create_or_update_subtasks(self):
        self.p_subtask = self.ensure_subtask(self.p_subtask, LLTaskMicrowavePulseSquare)

        # choose a resonator
        res_coupling = self.p_qubit.get_coupling('2Chi')

        self.p_subtask["Microwave Device"] = res_coupling[0]
        self.p_subtask["Readout"] = True

    def prepare_experiment(self):
        pass

    def submit_experiment(self):
        pass

    def process_experiment(self):
        pass

class LLTaskSingleQRotation(LLTask):
    def __init__(self, parent=None):
        super(LLTaskSingleQRotation,self).__init__(parent)

        self.p_qubit = None
        self.p_axis = 'X'
        self.p_angle = 0.

        self.add_parameter('p_qubit', label="Qubit Device", ptype=LLObjectParameter.PTYPE_LLOBJECT, select_from=LL.LL_ROOT.devices)
        self.add_parameter('p_axis', label="Rotation Axis", value_dict={'X':'X', 'Y':'Y', 'Z':'Z'})
        self.add_parameter('p_angle', label="Rotation Angle", unit='pi')

        self.p_subtask = None

        self.add_parameter('p_subtask', label="subtask", ptype=LLObjectParameter.PTYPE_LLOBJECT, viewable=False, read_only=True)


    def create_or_update_subtasks(self):

        if self.p_axis=='Z':
            self.p_subtask = self.ensure_subtask(self.p_subtask, LLTaskSingleQChangeBasis)

            self.p_subtask["Qubit Device"] = self.p_qubit
            self.p_subtask["Delta Phi"] = self.p_angle
        else:
            self.p_subtask = self.ensure_subtask(self.p_subtask, LLTaskSingleQPulseGen)

            self.p_subtask["Qubit Device"] = self.p_qubit
            self.p_subtask["Pulse Shape"]  = 'Square'
            if self.p_axis == 'X':
                self.p_subtask["Drive Axis Angle"] = 0.0
            else:
                self.p_subtask["Drive Axis Angle"] = 0.5
            self.p_subtask["Rotation Angle"] = self.p_angle
            self.p_subtask["Fixed Pulse Time (not Rate)"] = True
            self.p_subtask["Drive Time"] = 20.0e-9
            self.p_subtask["Drive Rate"] = 50.0e6 # will be ignored anyway

    def prepare_experiment(self):
        pass

    def submit_experiment(self):
        pass

    def process_experiment(self):
        pass

class LLTaskSingleQPulseGen(LLTask):
    def __init__(self, parent=None):
        super(LLTaskSingleQPulseGen,self).__init__(parent)

        self.p_qubit = None

        #pulse shaping parameters
        self.p_shape = 'Square'
        self.p_drive_phi = 0.
        self.p_theta = 0.

        self.p_fixed_time = False # use fixed time or fixed rate for gate
        self.p_rate = 100.0e+6 # rate to use if fixed_time=False
        self.p_time = 100.0e-9 # time to use if fixed_time=True

        self.add_parameter('p_qubit', label="Qubit Device", ptype=LLObjectParameter.PTYPE_LLOBJECT, select_from=LL.LL_ROOT.devices)
        self.add_parameter('p_shape', label="Pulse Shape", value_dict={'Square':'Square','Gaussian':'Gaussian'})
        self.add_parameter('p_drive_phi', label="Drive Axis Angle", unit='pi')
        self.add_parameter('p_theta', label="Rotation Angle", unit='pi')
        self.add_parameter('p_fixed_time', label="Fixed Pulse Time (not Rate)", read_only=True)
        self.add_parameter('p_rate', label="Drive Rate", unit='Hz')
        self.add_parameter('p_time', label="Drive Time", unit='s')

        self.p_subtask = None
        self.add_parameter('p_subtask', label="subtask", ptype=LLObjectParameter.PTYPE_LLOBJECT, viewable=False, read_only=True)


    def create_or_update_subtasks(self):

        if self.p_shape == 'Square':
            self.p_subtask = self.ensure_subtask(self.p_subtask, LLTaskMicrowavePulseSquare)
        else:
            self.p_subtask = self.ensure_subtask(self.p_subtask, LLTaskMicrowavePulseGaussian)

        self.p_subtask["Microwave Device"] = self.p_qubit
        if self.p_fixed_time:
            self.p_subtask["Pulse Length"] = self.p_time
            self.p_subtask["Pulse Power"] = 0
        else:
            self.p_subtask["Pulse Power"] = 0
            self.p_subtask["Pulse Length"] = 100.0e-9 #should calculate
        self.p_subtask["Pulse Phase"] = self.p_drive_phi

    def prepare_experiment(self):
        pass

    def submit_experiment(self):
        pass

    def process_experiment(self):
        pass

class LLTaskSingleQChangeBasis(LLTask):
    def __init__(self, parent=None):
        super(LLTaskSingleQChangeBasis,self).__init__(parent)

        self.p_qubit = None
        self.p_delta_phi = 0.

        self.add_parameter('p_qubit', label="Qubit Device", ptype=LLObjectParameter.PTYPE_LLOBJECT, select_from=LL.LL_ROOT.devices)
        self.add_parameter('p_delta_phi', label="Delta Phi", unit='pi')

    def create_or_update_subtasks(self):
        pass

    def prepare_experiment(self):
        pass

    def submit_experiment(self):
        self.p_qubit.s_phi_offset += self.p_delta_phi

    def process_experiment(self):
        pass
