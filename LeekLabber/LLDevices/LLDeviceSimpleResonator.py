from LeekLabber import *


class LLDeviceSimpleResonator(LLDevice):
    def __init__(self):
        super(LLDeviceSimpleResonator,self).__init__()

        ## Define parameters locally ##
        self.p_freq = 9.30e9 # Resonator frequency
        self.p_lifetime = 100e-9 # Resonator Radiative Lifetime
        self.p_single_photon_power = -70.0 # Power for steady state 1 photon at max IF amplitude

        ## Register these variables as parameters (these will be displayed in the GUI, stored in / restored by logs) ##
        self.add_parameter('p_freq', label='Frequency', unit='Hz')
        self.add_parameter('p_lifetime', label='Lifetime', unit='s')
        self.add_parameter('p_single_photon_power', label='Single Photon Power', unit='dBm')
