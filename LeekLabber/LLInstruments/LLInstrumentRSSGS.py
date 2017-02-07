from LeekLabber import *

class LLInstrumentRSSGS(LLInstrument):
    def __init__(self):
        super(LLInstrumentRSSGS,self).__init__()

        ## Define parameters locally ##
        self.p_freq = 6.100e9 # Synthesized frequency
        self.p_pow  = -60.0 # Output power
        self.p_iq_mod = False # Enable/Disable IQ Modulation
        self.p_output = False # Enable/Disable Output

        ## Register these variables as parameters (these will be displayed in the GUI, stored in / restored by logs) ##
        self.add_parameter('p_freq', label='Frequency', unit='Hz')
        self.add_parameter('p_pow', label='Power', unit='dBm')
        self.add_parameter('p_iq_mod', label='IQ Modulation')
        self.add_parameter('p_output', label='Output')
