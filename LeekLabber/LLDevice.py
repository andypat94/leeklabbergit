from LeekLabber import *
import LeekLabber as LL

class LLDevice(LLObject):
    def __init__(self):
        super(LLDevice, self).__init__(LL.LL_ROOT.devices)

        self.p_couplings = []

        self.add_parameter('p_couplings', label="Couplings", ptype=LLObjectParameter.PTYPE_LLOBJECT_LIST)

class LLDeviceCoupling(LLObject):
    def __init__(self, objA=None, objB=None, value=0.0, coupling_type='g',unit='Hz'):
        super(LLDeviceCoupling, self).__init__(LL.LL_ROOT.couplings)

        self.p_devA = objA
        self.p_devB = objB
        self.p_value = value
        self.p_coupling_type = coupling_type

        self.add_parameter('p_devA', label="Device A", ptype=LLObjectParameter.PTYPE_LLOBJECT, onChange=self.couplings_changed)
        self.add_parameter('p_devB', label="Device B", ptype=LLObjectParameter.PTYPE_LLOBJECT, onChange=self.couplings_changed)
        self.add_parameter('p_value', label="Coupling Strength", unit=unit)
        self.add_parameter('p_coupling_type', label="Coupling Type")

        self.prev_devA = None
        self.prev_devB = None

        self.couplings_changed()

    def couplings_changed(self):
        def update_coupling_lists(dev,prev):
            if dev != prev:
                if prev is None:
                    pass
                else:
                    prev["Couplings"] = [coupling for coupling in prev["Couplings"] if coupling != self]
                if dev is None:
                    pass
                else:
                    dev["Couplings"] += [self,]
        update_coupling_lists(self.p_devA,self.prev_devA)
        update_coupling_lists(self.p_devB,self.prev_devB)

