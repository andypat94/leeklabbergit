import  LeekLabber as LL

class LLRoot(LL.LLObject):
    def __init__(self):
        super(LLRoot, self).__init__(None)
        self.devices = None
        self.instruments = None
        self.expsetups = None
        self.couplings = None
        self.task = None
        self.pulses = None

        self.add_parameter("devices",label="Devices",ptype=LL.LLObjectParameter.PTYPE_LLOBJECT)
        self.add_parameter("instruments",label="Instruments",ptype=LL.LLObjectParameter.PTYPE_LLOBJECT)
        self.add_parameter("expsetups",label="Experiment Setups",ptype=LL.LLObjectParameter.PTYPE_LLOBJECT)
        self.add_parameter("couplings",label="Couplings",ptype=LL.LLObjectParameter.PTYPE_LLOBJECT)
        self.add_parameter("task",label="Task",ptype=LL.LLObjectParameter.PTYPE_LLOBJECT)
        self.add_parameter("pulses",label="Pulses",ptype=LL.LLObjectParameter.PTYPE_LLOBJECT)

    @staticmethod
    def from_blank():
        root = LLRoot()
        root.devices = LL.LLObject(root)
        root.instruments = LL.LLObject(root)
        root.expsetups = LL.LLObject(root)
        root.couplings = LL.LLObject(root)
        root.task = LL.LLTaskDelay(root)
        root.pulses = LL.LLObject(root)
        return root

