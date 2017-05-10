from LeekLabber import *
import LeekLabber as LL


class LLInstrument(LLObject):
    def __init__(self):
        super(LLInstrument,self).__init__(LL.LL_ROOT.instruments)
        self.p_name = 'default'
        self.p_addr = 'default'
        self.add_parameter('p_name', label="Instrument Name")
        self.add_parameter('p_addr', label="Instrument Address")

    def setup_internal(self):
        self.setup_instrument()

    def setup_instrument(self):
        pass

    def readout_internal(self):
        self.readout_instrument()

    def readout_instrument(self):
        pass