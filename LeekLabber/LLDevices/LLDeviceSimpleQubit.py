from LeekLabber import *


class LLDeviceSimpleQubit(LLMicrowaveDevice):
    def __init__(self):
        super(LLDeviceSimpleQubit,self).__init__()

        ## Define parameters locally ##
        self.p_t1 = 10.0e-6 # Qubit T1
        self.p_t2 = 12.0e-6 # Qubit T2

        self.p_rabirate = 100.0e6 # Qubit rabi rate with max IF amp
        self.p_rabirate_lo_power = 20.0 # Qubit Drive LO Power for given rabi rate

        ## Register these variables as parameters (these will be displayed in the GUI, stored in / restored by logs) ##
        self.add_parameter('p_t1', label='T1', unit='s')
        self.add_parameter('p_t2', label='T2', unit='s')

        self.add_parameter('p_rabirate', label='Rabi Rate', unit='Hz')
        self.add_parameter('p_rabirate_lo_power', label='Rabi Rate LO Power', unit='dBm')

