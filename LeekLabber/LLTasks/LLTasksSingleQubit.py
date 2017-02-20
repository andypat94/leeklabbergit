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
        self.p_qubit.s_phi_offset += self.p_delta_phi

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

        self.pulse1 = self.add_pulse()
        self.pulse2 = self.add_pulse()
        self.pulse3 = self.add_pulse()

    def prepare_experiment(self):
        self.prepare_pulse(self.pulse1, self.p_qubit, self.p_qubit["Frequency"], 20.0, True, False)
        # Ask experimental setup to prepare to send a microwave drive at this frequency, power etc.
        #self.prepare_microwave_drive(self.p_qubit,self.p_qubit["Frequency"], power=20.0, pulsed=True, measured=False)
        #self.prepare_pulse(self.pulse2, self.p_qubit,self.p_qubit["Frequency"]-300.0e6, power=20.0, pulsed=True, measured=False)
        self.prepare_pulse(self.pulse2, self.p_qubit, self.p_qubit["Frequency"], -25.0, False, False)
        self.prepare_pulse(self.pulse3, self.p_qubit, 10.0e9, power=-60.0, pulsed=True, measured=True)

    def submit_experiment(self):
        # do a pulse
        #t = self.get_timebase(self.pulse1, 100.0e-9)
        #i = np.zeros(len(t))
        #q = np.zeros(len(t))
        #i.fill(np.cos(self.p_phase*np.pi))
        #q.fill(np.sin(self.p_phase*np.pi))
        #self.submit_pulse(self.pulse1, i, q, self.p_qubit.s_phi_offset)

        t = self.get_timebase(self.pulse3, 200.0e-9)
        i = np.zeros(len(t))
        q = np.zeros(len(t))
        self.submit_pulse(self.pulse3, i, q, 0.)

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