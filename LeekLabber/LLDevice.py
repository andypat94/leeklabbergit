from LeekLabber import *
import LeekLabber as LL

class LLDevice(LLObject):
    def __init__(self):
        super(LLDevice, self).__init__(LL.LL_ROOT.devices)

        self.p_name = "Device Name"

        self.add_parameter("p_name",label="Device Name")

        self.couplings = []

    def clear_coupling_refs(self):
        del self.couplings[:]

    def add_coupling_ref(self, coupling):
        self.couplings.append(coupling)

    def clear_mwcl_refs(self):
        pass

    def set_control_line(self):
        pass

    def get_couplings(self, type):
        print len(self.couplings)
        return [coupling for coupling in self.couplings if coupling.p_coupling_type==type]

    def get_coupling(self, type):
        couplings = self.get_couplings(type)
        if len(couplings)>0:
            coupling = couplings[0]
            if coupling.p_devA == self:
                return (coupling.p_devB, coupling)
            else:
                return (coupling.p_devA, coupling)
        else:
            return (None, None)


class LLMicrowaveDevice(LLDevice):
    def __init__(self):
        super(LLMicrowaveDevice, self).__init__()
        self.p_freq = 6.100e9 # MW default drive frequency

        self.add_parameter('p_freq', label='Frequency', unit='Hz')
        self.mwcls = []

    def clear_mwcl_refs(self):
        del self.mwcls[:]

    def add_mwcl_ref(self, mwcl):
        self.mwcls.append(mwcl)

    #TODO: choose control line more intelligently from a list??
    def set_control_line(self):
        if(len(self.mwcls)>0):
            self.mwcl = self.mwcls[0]
        else:
            self.mwcl =  None

    def prepare_pulse(self, pulse):
        self.mwcl.prepare_pulse(pulse)

    def clear_state_vars(self):
        pass

class LLDeviceCoupling(LLObject):
    def __init__(self, objA=None, objB=None, value=0.0, coupling_type='2Chi',unit='Hz'):
        super(LLDeviceCoupling, self).__init__(LL.LL_ROOT.couplings)

        self.p_devA = objA
        self.p_devB = objB
        self.p_value = value
        self.p_coupling_type = coupling_type

        self.add_parameter('p_devA', label="Device A", ptype=LLObjectParameter.PTYPE_LLOBJECT, select_from=LL.LL_ROOT.devices) #, onChange=self.couplings_changed)
        self.add_parameter('p_devB', label="Device B", ptype=LLObjectParameter.PTYPE_LLOBJECT, select_from=LL.LL_ROOT.devices) #, onChange=self.couplings_changed)
        self.add_parameter('p_value', label="Coupling Strength", unit=unit)
        self.add_parameter('p_coupling_type', label="Coupling Type", value_dict={'2Chi':'2Chi','J':'J'})

    def add_coupling_refs(self):
        if (self.p_devA is not None) and (self.p_devB is not None):
            self.p_devA.add_coupling_ref(self)
            self.p_devB.add_coupling_ref(self)