from LeekLabber import *
from LLSimpleTasks import *
import LeekLabber as LL

class LLTaskMicrowavePulseSquare(LLTask):
    def __init__(self, parent = None):
        super(LLTaskMicrowavePulseSquare, self).__init__(parent)

        self.p_qubit = None
        self.p_length= 0.
        self.p_power=0.
        self.p_phase= 0.
        self.p_readout = False

        self.add_parameter('p_qubit', label="Microwave Device", ptype=LLObjectParameter.PTYPE_LLOBJECT, select_from=LL.LL_ROOT.devices)
        self.add_parameter('p_length', label="Pulse Length", unit='s')
        self.add_parameter('p_power', label="Pulse Power", unit='dBm')
        self.add_parameter('p_phase', label="Pulse Phase", unit='pi')
        self.add_parameter('p_readout', label="Readout")

        self.pulse1 = self.add_pulse()

    def prepare_experiment(self):
        self.prepare_pulse(self.pulse1, self.p_qubit, self.p_qubit["Frequency"], self.p_power, True, self.p_readout)

    def submit_experiment(self):
        t = self.get_timebase(self.pulse1, self.p_length)
        i = np.empty(len(t))
        q = np.empty(len(t))
        i.fill(np.cos(np.pi*self.p_phase))
        q.fill(np.sin(np.pi*self.p_phase))
        self.submit_pulse(self.pulse1, i, q, 0);#todo:self.p_qubit.s_phi_offset)

    def create_or_update_subtasks(self):
        pass

    def process_experiment(self):
        pass

class LLTaskMicrowavePulseGaussian(LLTask):
    def __init__(self, parent = None):
        super(LLTaskMicrowavePulseGaussian, self).__init__(parent)

        self.p_qubit = None
        self.p_length= 0.
        self.p_power= 0.
        self.p_phase= 0.

        self.add_parameter('p_qubit', label="Microwave Device", ptype=LLObjectParameter.PTYPE_LLOBJECT, select_from = LL.LL_ROOT.devices)
        self.add_parameter('p_length', label="Pulse Length", unit='s')
        self.add_parameter('p_power', label="Pulse Power", unit='dBm')
        self.add_parameter('p_phase', label="Pulse Phase", unit='pi')

    def create_or_update_subtasks(self):
        pass

    def prepare_experiment(self):
        pass

    def submit_experiment(self):
        pass

    def process_experiment(self):
        pass