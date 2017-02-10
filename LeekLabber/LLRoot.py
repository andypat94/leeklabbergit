from LeekLabber import *

class LLRoot(LLObject):
    def __init__(self):
        super(LLRoot, self).__init__(None)
        self.devices = None
        self.instruments = None
        self.expsetups = None
        self.couplings = None
        self.task = None

        self.add_parameter("devices",label="Devices",ptype=LLObjectParameter.PTYPE_LLOBJECT)
        self.add_parameter("instruments",label="Instruments",ptype=LLObjectParameter.PTYPE_LLOBJECT)
        self.add_parameter("expsetups",label="Experiment Setups",ptype=LLObjectParameter.PTYPE_LLOBJECT)
        self.add_parameter("couplings",label="Couplings",ptype=LLObjectParameter.PTYPE_LLOBJECT)
        self.add_parameter("task",label="Task",ptype=LLObjectParameter.PTYPE_LLOBJECT)

    @staticmethod
    def from_blank():
        root = LLRoot()
        root.devices = LLObject(root)
        root.instruments = LLObject(root)
        root.expsetups = LLObject(root)
        root.couplings = LLObject(root)
        root.task = LLTask(root)
        return root