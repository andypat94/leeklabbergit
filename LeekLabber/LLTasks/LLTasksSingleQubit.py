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

    def create_or_update_subtasks(self):
        if self.p_axis=='Z':
            if len(self.ll_children) == 0:
                subtask = LLTaskSingleQChangeBasis(self)
            else:
                subtask = self.ll_children[0]
                if isinstance(subtask, LLTaskSingleQChangeBasis):
                    pass
                else:
                    subtask.remove()
                    subtask = LLTaskSingleQChangeBasis(self)

            subtask["Qubit Device"] = self.p_qubit
            subtask["Delta Phi"] = self.p_angle
        else:
            if len(self.ll_children) == 0:
                subtask = LLTaskSingleQPulseGen(self)
            else:
                subtask = self.ll_children[0]
                if isinstance(subtask, LLTaskSingleQPulseGen):
                    pass
                else:
                    subtask.remove()
                    subtask = LLTaskSingleQPulseGen(self)

            subtask["Qubit Device"] = self.p_qubit
            subtask["Pulse Shape"]  = 'Square'
            if self.p_axis == 'X':
                subtask["Drive Axis Angle"] = 0.0
            else:
                subtask["Drive Axis Angle"] = 0.5
            subtask["Rotation Angle"] = self.p_angle
            subtask["Fixed Pulse Time (not Rate)"] = True
            subtask["Drive Time"] = 20.0e-9
            subtask["Drive Rate"] = 50.0e6 # will be ignored anyway

        super(LLTaskSingleQRotation, self).create_or_update_subtasks() # will update children tasks as well.


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

    def create_or_update_subtasks(self):
        if self.p_shape == 'Square':
            if len(self.ll_children) == 0:
                subtask = LLTaskSingleQPulseSquare(self)
            else:
                subtask = self.ll_children[0]
                if isinstance(subtask, LLTaskSingleQPulseSquare):
                    pass
                else:
                    subtask.remove()
                    subtask = LLTaskSingleQPulseSquare(self)
        else:
            if len(self.ll_children) == 0:
                subtask = LLTaskSingleQPulseGaussian(self)
            else:
                subtask = self.ll_children[0]
                if isinstance(subtask, LLTaskSingleQPulseGaussian):
                    pass
                else:
                    subtask.remove()
                    subtask = LLTaskSingleQPulseGaussian(self)

        subtask["Qubit Device"] = self.p_qubit
        if self.p_fixed_time:
            subtask["Pulse Length"] = self.p_time
            subtask["Pulse Amplitude"] = 1.0 #should calculate
        else:
            subtask["Pulse Amplitude"] = self.p_rate
            subtask["Pulse Length"] = 100.0e-9 #should calculate
        subtask["Pulse Phase"] = self.p_drive_phi

        super(LLTaskSingleQPulseGen, self).create_or_update_subtasks()

class LLTaskSingleQChangeBasis(LLTask):
    def __init__(self, parent=None):
        super(LLTaskSingleQChangeBasis,self).__init__(parent)

        self.p_qubit = None
        self.p_delta_phi = 0.

        self.add_parameter('p_qubit', label="Qubit Device", ptype=LLObjectParameter.PTYPE_LLOBJECT)
        self.add_parameter('p_delta_phi', label="Delta Phi", unit='pi')

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
        self.p_qubit.prepare_microwave_drive(freq=10.0e9, power=20.0, pulsed=True, measured=True)
        self.p_qubit.prepare_microwave_drive(freq=6.1e9, power=20.0, pulsed=True, measured=False)
        self.p_qubit.prepare_microwave_drive(freq=6.4e9, power=20.0, pulsed=True, measured=False)
        #self.p_qubit.prepare_microwave_drive(freq=10.9e9, power=20.0, pulsed=True, measured=False)
        #self.p_qubit.prepare_microwave_drive(freq=10.9e9, power=20.0, pulsed=True, measured=False)

        # allow any child tasks to be processed
        super(LLTaskSingleQPulseSquare,self).prepare_experiment()

    def submit_experiment(self):

        t = self.p_qubit.get_timebase(self.p_length, self.p_qubit["Frequency"], 20.0) # get timebase for required pulse time, freq, power
        if t is None:
            t = np.arange(1000.,dtype='double')
        i = np.empty(len(t),dtype='double')
        q = np.empty(len(t),dtype='double')
        i.fill(np.cos(self.p_phase*np.pi))
        q.fill(np.sin(self.p_phase*np.pi))
        self.p_qubit.submit_pulse(i, q, self.p_qubit["Frequency"], 20.0) # default frequency is just the microwave device frequency

        # allow any child tasks to be processed
        super(LLTaskSingleQPulseSquare,self).submit_experiment()

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
