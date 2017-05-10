from LeekLabber import *

class LLTaskDelay(LLTask):
    def __init__(self, parent=None):
        super(LLTaskDelay,self).__init__(parent)

        self.p_delay = 10.0e-6

        self.add_parameter('p_delay', label="Delay Time", unit='s')

    def create_or_update_subtasks(self):
        pass

    def prepare_experiment(self):
        pass

    def submit_experiment(self):
        self.submit_delay(self.p_delay)

    def process_experiment(self):
        pass

class LLContinuousDrive(LLTask):
    def __init__(self, parent=None):
        super(LLContinuousDrive, self).__init__(parent)

        self.p_device = None
        self.p_use_device_freq = True
        self.p_freq = 0.0
        self.p_readout = False
        self.p_power = 0.0

        self.add_parameter('p_device', label="Microwave Device", ptype=LLObjectParameter.PTYPE_LLOBJECT, select_from=LL.LL_ROOT.devices)
        self.add_parameter('p_readout', label="Measure Response")
        self.add_parameter('p_use_device_freq', label="Use Device Frequency")
        self.add_parameter('p_freq', label="Custom Frequency", unit='Hz')
        self.add_parameter('p_power', label="Power", unit='dBm')

        self.pulse1 = self.add_pulse()

    def create_or_update_subtasks(self):
        pass

    def prepare_experiment(self):
        if self.p_use_device_freq:
            self.drive_freq = self.p_device.p_freq
        else:
            self.drive_freq = self.p_freq
        self.prepare_pulse(self.pulse1, self.p_device, self.drive_freq, self.p_power, False, self.p_readout)

    def submit_experiment(self):
        pass

    def process_experiment(self):
        pass


class LLSimplePulse(LLTask):
    def __init__(self, parent=None):
        super(LLSimplePulse,self).__init__(parent)

        self.p_device = None
        self.p_use_device_freq = True
        self.p_freq = 0.0
        self.p_readout = False

        #pulse shaping parameters
        self.p_shape = 'Square'
        self.p_phi = 0.
        self.p_power = 0.
        self.p_width = 0.
        self.p_transition = 0. #only used for tanh
        self.p_trunc = 2.

        self.add_parameter('p_device', label="Microwave Device", ptype=LLObjectParameter.PTYPE_LLOBJECT, select_from=LL.LL_ROOT.devices)
        self.add_parameter('p_readout', label="Measure Response")
        self.add_parameter('p_use_device_freq', label="Use Device Frequency")
        self.add_parameter('p_freq', label="Custom Frequency", unit='Hz')
        self.add_parameter('p_shape', label="Shape", value_dict={'Square':'Square','Gaussian':'Gaussian','Tanh':'Tanh','SetupAndHold':'SetupAndHold'})
        self.add_parameter('p_phi', label="Phi", unit='pi')
        self.add_parameter('p_power', label="Power", unit='dBm')
        self.add_parameter('p_width', label="Width", unit='s')
        self.add_parameter('p_trunc', label="Truncation Range", unit='width(s)')
        self.add_parameter('p_transition', label='Transition Time', unit='s')

        self.pulse1 = self.add_pulse()

    def create_or_update_subtasks(self):
        pass

    def prepare_experiment(self):
        if self.p_use_device_freq:
            self.drive_freq = self.p_device.p_freq
        else:
            self.drive_freq = self.p_freq
        self.prepare_pulse(self.pulse1, self.p_device, self.drive_freq, self.p_power, True, self.p_readout)

    def submit_experiment(self):
        t = self.get_timebase(self.pulse1, self.p_width)
        i=np.ones(len(t))
        q=np.zeros(len(t))
        self.submit_pulse(self.pulse1, i, q, self.p_phi)

    def process_experiment(self):
        pass
