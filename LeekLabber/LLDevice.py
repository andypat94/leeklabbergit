from LeekLabber import *
import LeekLabber as LL

class LLDevice(LLObject):
    def __init__(self):
        super(LLDevice, self).__init__(LL.LL_ROOT.devices)

        self.couplings = []

    def clear_coupling_refs(self):
        self.couplings = []

    def add_coupling_ref(self, coupling):
        self.couplings.append(coupling)

    def clear_mwcl_refs(self):
        pass

    def set_control_line(self):
        pass


class LLMicrowaveDevice(LLDevice):
    def __init__(self):
        super(LLMicrowaveDevice, self).__init__()
        self.p_freq = 6.100e9 # MW default drive frequency

        self.add_parameter('p_freq', label='Frequency', unit='Hz')
        self.mwcls = []

    def clear_mwcl_refs(self):
        self.mwcls = []

    def add_mwcl_ref(self, mwcl):
        self.mwcls.append(mwcl)

    #TODO: choose control line more intelligently from a list??
    def set_control_line(self):
        if(len(self.mwcls)>0):
            self.mwcl = self.mwcls[0]
        else:
            self.mwcl =  None

    def prepare_microwave_drive(self, freq, power, pulsed, measured):
        self.mwcl.prepare_microwave_drive(freq, power, pulsed, measured, self)

    def get_timeslot(self, time, freq, power):
        return self.mwcl.get_timebase(time, freq, power)

    def submit_pulse(self, DC_I, DC_Q, freq, power):
        self.mwcl.submit_pulse(DC_I, DC_Q, freq, self)

class LLDeviceCoupling(LLObject):
    def __init__(self, objA=None, objB=None, value=0.0, coupling_type='g',unit='Hz'):
        super(LLDeviceCoupling, self).__init__(LL.LL_ROOT.couplings)

        self.p_devA = objA
        self.p_devB = objB
        self.p_value = value
        self.p_coupling_type = coupling_type

        self.add_parameter('p_devA', label="Device A", ptype=LLObjectParameter.PTYPE_LLOBJECT) #, onChange=self.couplings_changed)
        self.add_parameter('p_devB', label="Device B", ptype=LLObjectParameter.PTYPE_LLOBJECT) #, onChange=self.couplings_changed)
        self.add_parameter('p_value', label="Coupling Strength", unit=unit)
        self.add_parameter('p_coupling_type', label="Coupling Type")

    def add_coupling_refs(self):
        if (self.p_devA is not None) and (self.p_devB is not None):
            self.p_devA.add_coupling_ref(self)
            self.p_devB.add_coupling_ref(self)