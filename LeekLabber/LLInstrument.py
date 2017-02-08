from LeekLabber import *


class LLInstrument(LLObject):
    def __init__(self):
        super(LLInstrument,self).__init__()
        self.p_name = 'default'
        self.p_addr = 'default'
        self.add_parameter('p_name', label="Instrument Name")
        self.add_parameter('p_addr', label="Instrument Address")

