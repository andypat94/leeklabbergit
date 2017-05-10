from LeekLabber import *
from LLSimpleTasks import *
#from LLMicrowaveTasks import *
import LeekLabber as LL
from math import log10

class LLTaskSingleQMeasure(LLTask):
    def __init__(self, parent=None):
        super(LLTaskSingleQMeasure, self).__init__(parent)
        self.p_qubit = None
        self.add_parameter('p_qubit', label="Qubit Device", ptype=LLObjectParameter.PTYPE_LLOBJECT, select_from=LL.LL_ROOT.devices)

        self.p_subtask = None
        self.add_parameter('p_subtask', label="subtask", ptype=LLObjectParameter.PTYPE_LLOBJECT, viewable=False, read_only=True)

    def create_or_update_subtasks(self):
        self.p_subtask = self.ensure_subtask(self.p_subtask, LLSimplePulse)

        # choose a resonator
        res_coupling = self.p_qubit.get_coupling('2Chi')
        self.resonator = res_coupling[0]

        self.p_subtask["Microwave Device"] = self.resonator
        self.p_subtask["Measure Response"] = True
        self.p_subtask["Use Device Frequency"] = True
        self.p_subtask["Shape"] = "Square"
        self.p_subtask["Power"]  = self.resonator["Single Photon Power"]
        self.p_subtask["Width"] = self.p_qubit.p_t1

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
        self.p_modulate_power = True

        self.add_parameter('p_qubit', label="Qubit Device", ptype=LLObjectParameter.PTYPE_LLOBJECT, select_from=LL.LL_ROOT.devices)
        self.add_parameter('p_axis', label="Rotation Axis", value_dict={'X':'X', 'Y':'Y', 'Z':'Z'})
        self.add_parameter('p_angle', label="Rotation Angle", unit='pi')
        self.add_parameter('p_modulate_power', label="Modulation", value_dict={'Power':True, 'Width':False})

        self.p_subtask = None

        self.add_parameter('p_subtask', label="subtask", ptype=LLObjectParameter.PTYPE_LLOBJECT, viewable=False, read_only=True)


    def create_or_update_subtasks(self):

        if self.p_axis=='Z':
            self.p_subtask = self.ensure_subtask(self.p_subtask, LLTaskSingleQChangeBasis)

            self.p_subtask["Qubit Device"] = self.p_qubit
            self.p_subtask["Delta Phi"] = self.p_angle
        else:
            self.p_subtask = self.ensure_subtask(self.p_subtask, LLTaskSingleQPulseGen)

            self.p_subtask.p_qubit = self.p_qubit
            self.p_subtask.p_shape = self.p_qubit.p_calib_shape
            self.p_subtask.p_trunc = self.p_qubit.p_calib_truncation
            self.p_subtask.p_transition = self.p_qubit.p_calib_transition

            modangle = abs(self.p_angle)
            sign = self.p_angle >= 0.0

            if modangle == 1.0: # pi rotation
                self.p_subtask.p_power = self.p_qubit.p_calib_power_pi
                self.p_subtask.p_width = self.p_qubit.p_calib_width_pi
            elif modangle == 0.5: # pi/2 rotation
                self.p_subtask.p_power = self.p_qubit.p_calib_power_pi2
                self.p_subtask.p_width = self.p_qubit.p_calib_width_pi2
            else:
                if self.p_modulate_power:
                    self.p_subtask.p_width =  self.p_qubit.p_calib_width_pi
                    if modangle>0.0:
                        self.p_subtask.p_power = self.p_qubit.p_calib_power_pi + 20.0*log10(modangle)
                    else:
                        self.p_subtask.p_power = self.p_qubit.p_calib_power_pi + 20.0*log10(1e-3) #todo: prettier solution?
                else:
                    self.p_subtask.p_power = self.p_qubit.p_calib_power_pi
                    self.p_subtask.p_width = self.p_qubit.p_calib_width_pi * modangle

            if self.p_axis=='X':
                if sign:
                    self.p_subtask.p_phi = 0.0
                else:
                    self.p_subtask.p_phi = 1.0
            else: # Y Axis
                if sign:
                    self.p_subtask.p_phi = 0.5
                else:
                    self.p_subtask.p_phi = 1.5


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
        self.p_phi = 0.
        self.p_power = 0.
        self.p_width = 0.
        self.p_transition = 0. #only used for tanh
        self.p_trunc = 2.

        self.add_parameter('p_qubit', label="Qubit Device", ptype=LLObjectParameter.PTYPE_LLOBJECT, select_from=LL.LL_ROOT.devices)
        self.add_parameter('p_shape', label="Shape", value_dict={'Square':'Square','Gaussian':'Gaussian','Tanh':'Tanh','DRAG':'DRAG','hDRAG':'hDRAG'})
        self.add_parameter('p_phi', label="Phi", unit='pi')
        self.add_parameter('p_power', label="Power", unit='dBm')
        self.add_parameter('p_width', label="Width", unit='s')
        self.add_parameter('p_trunc', label="Truncation Range", unit='width(s)')
        self.add_parameter('p_transition', label='Transition Time', unit='s')

        self.pulse1 = self.add_pulse()

    def create_or_update_subtasks(self):
        pass

    def prepare_experiment(self):
        self.prepare_pulse(self.pulse1, self.p_qubit, self.p_qubit.p_freq, self.p_power, True, False)

    def submit_experiment(self):

        if self.p_shape=='Gaussian':
            t0 = self.p_width/2.0
            l = self.p_width*self.p_trunc
            t1 = l/2.
            t = self.get_timebase(self.pulse1, l)
            i = np.exp(-np.power((t-t1)/t0,2))
            q = np.zeros(len(t))
        elif self.p_shape=='Tanh':
            t0 = self.p_trunc*self.p_transition
            t1 = t0 + self.p_width
            l = t1 + t0
            t = self.get_timebase(self.pulse1, l)
            i = 0.5*(np.tanh((t-t0)/self.p_transition)-np.tanh((t-t1)/self.p_transition))
            q = np.zeros(len(t))
        else: # default to square
            t = self.get_timebase(self.pulse1, self.p_width)
            i = np.ones(len(t))
            q = np.zeros(len(t))

        self.submit_pulse(self.pulse1, i, q, self.p_phi + self.p_qubit.s_phi_offset)

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
        self.p_qubit.s_phi_offset -= self.p_delta_phi

    def process_experiment(self):
        pass
