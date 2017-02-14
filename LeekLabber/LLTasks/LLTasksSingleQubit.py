from LeekLabber import *


class LLTaskSingleQRotation(LLTask):
    def __init__(self, parent=None):
        super(LLTaskSingleQRotation,self).__init__(parent)

        self.p_qubit = None
        self.p_axis = 'X'
        self.p_angle = 0.

        self.add_parameter('p_qubit', label="Qubit Device", ptype=LLObjectParameter.PTYPE_LLOBJECT)
        self.add_parameter('p_axis', label="Rotation Axis", value_list=['X','Y','Z'])
        self.add_parameter('p_angle', label="Rotation Angle", unit='pi')

        self.p_subtask = None

        self.add_parameter('p_subtask', label="subtask", ptype=LLObjectParameter.PTYPE_LLOBJECT)


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

        self.add_parameter('p_qubit', label="Qubit Device", ptype=LLObjectParameter.PTYPE_LLOBJECT)
        self.add_parameter('p_shape', label="Pulse Shape", value_list=['Square','Gaussian'])
        self.add_parameter('p_drive_phi', label="Drive Axis Angle", unit='pi')
        self.add_parameter('p_theta', label="Rotation Angle", unit='pi')
        self.add_parameter('p_fixed_time', label="Fixed Pulse Time (not Rate)")
        self.add_parameter('p_rate', label="Drive Rate", unit='Hz')
        self.add_parameter('p_time', label="Drive Time", unit='s')

        self.p_subtask = None
        self.add_parameter('p_subtask', label="subtask", ptype=LLObjectParameter.PTYPE_LLOBJECT)

    def create_or_update_subtasks(self):

        if self.p_shape == 'Square':
            self.p_subtask = self.ensure_subtask(self.p_subtask, LLTaskSingleQPulseSquare)
        else:
            self.p_subtask = self.ensure_subtask(self.p_subtask, LLTaskSingleQPulseGaussian)

        self.p_subtask["Qubit Device"] = self.p_qubit
        if self.p_fixed_time:
            self.p_subtask["Pulse Length"] = self.p_time
            self.p_subtask["Pulse Amplitude"] = 1.0 #should calculate
        else:
            self.p_subtask["Pulse Amplitude"] = self.p_rate
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

        self.add_parameter('p_qubit', label="Qubit Device", ptype=LLObjectParameter.PTYPE_LLOBJECT)
        self.add_parameter('p_delta_phi', label="Delta Phi", unit='pi')

    def create_or_update_subtasks(self):
        pass

    def prepare_experiment(self):
        pass

    def submit_experiment(self):
        pass

    def process_experiment(self):
        pass

class LLTaskSingleQPulseSquare(LLTask):
    def __init__(self, parent = None):
        super(LLTaskSingleQPulseSquare, self).__init__(parent)

        self.p_qubit = None
        self.p_length= 0.
        self.p_amplitude= 0.
        self.p_phase= 0.

        self.add_parameter('p_qubit', label="Qubit Device", ptype=LLObjectParameter.PTYPE_LLOBJECT)
        self.add_parameter('p_length', label="Pulse Length", unit='s')
        self.add_parameter('p_amplitude', label="Pulse Amplitude", unit='V')
        self.add_parameter('p_phase', label="Pulse Phase", unit='pi')

    def prepare_experiment(self):
        # Ask experimental setup to prepare to send a microwave drive at this frequency, power etc.
        self.prepare_microwave_drive(self.p_qubit,freq=6.2e9, power=20.0, pulsed=True, measured=False)
        self.prepare_microwave_drive(self.p_qubit,freq=10.0e9, power=20.0, pulsed=True, measured=True)
        self.prepare_microwave_drive(self.p_qubit,freq=6.1e9, power=20.0, pulsed=True, measured=False)
        self.prepare_microwave_drive(self.p_qubit,freq=6.4e9, power=20.0, pulsed=True, measured=False)
        #self.p_qubit.prepare_microwave_drive(freq=10.9e9, power=20.0, pulsed=True, measured=False)
        #self.p_qubit.prepare_microwave_drive(freq=10.9e9, power=20.0, pulsed=True, measured=False)

    def submit_experiment(self):
        # do a pulse
        t = self.get_timeslot(self.p_qubit, self.p_length, self.p_qubit["Frequency"], 20.0) # get timebase for required pulse time, freq, power
        i = np.empty(len(t),dtype='double')
        q = np.empty(len(t),dtype='double')
        i.fill(np.cos(self.p_phase*np.pi))
        q.fill(np.sin(self.p_phase*np.pi))
        self.submit_pulse(self.p_qubit, i, q, self.p_qubit["Frequency"], 20.0) # default frequency is just the microwave device frequency

    def create_or_update_subtasks(self):
        pass

    def process_experiment(self):
        pass

class LLTaskSingleQPulseGaussian(LLTask):
    def __init__(self, parent = None):
        super(LLTaskSingleQPulseGaussian, self).__init__(parent)

        self.p_qubit = None
        self.p_length= 0.
        self.p_amplitude= 0.
        self.p_phase= 0.

        self.add_parameter('p_qubit', label="Qubit Device", ptype=LLObjectParameter.PTYPE_LLOBJECT)
        self.add_parameter('p_length', label="Pulse Length", unit='s')
        self.add_parameter('p_amplitude', label="Pulse Amplitude", unit='V')
        self.add_parameter('p_phase', label="Pulse Phase", unit='pi')

    def create_or_update_subtasks(self):
        pass

    def prepare_experiment(self):
        pass

    def submit_experiment(self):
        pass

    def process_experiment(self):
        pass