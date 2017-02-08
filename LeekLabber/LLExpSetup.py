from LeekLabber import *

class LLMicrowaveControlLine(LLObject):
    def __init__(self, NDrives=2, NReadouts=1):
        super(LLMicrowaveControlLine, self).__init__()

        # Add local parameters
        self.p_n_drives = NDrives
        self.p_n_readouts = NReadouts
        self.p_dac_data = [None]*NDrives
        self.p_adc_data = [None]*NReadouts
        self.p_dac_channel_i = np.arange(self.p_n_drives,dtype='int')
        self.p_dac_channel_q = np.arange(self.p_n_drives,dtype='int')
        self.p_adc_channel_i = np.arange(self.p_n_readouts,dtype='int')
        self.p_adc_channel_q = np.arange(self.p_n_readouts,dtype='int')
        self.p_s21_not_s11 = True
        self.p_devices = []

        # Register parameters
        self.add_parameter('p_n_drives',label="Number of Drives")
        self.add_parameter('p_dac_data',label='DACs for Drives',ptype=LLObjectParameter.PTYPE_LLPARAMETER_LIST)
        self.add_parameter('p_dac_channel_i',label="DAC Channel I")
        self.add_parameter('p_dac_channel_q',label="DAC Channel Q")
        self.add_parameter('p_n_readouts',label="Number of Readouts")
        self.add_parameter('p_adc_data',label='ADCs for Readouts',ptype=LLObjectParameter.PTYPE_LLPARAMETER_LIST)
        self.add_parameter('p_adc_channel_i',label="ADC Channel I")
        self.add_parameter('p_adc_channel_q',label="ADC Channel Q")
        self.add_parameter('p_s21_not_s11', label="Transmission (Not Reflection)")
        self.add_parameter('p_devices', label="Connected Devices",ptype=LLObjectParameter.PTYPE_LLOBJECT_LIST)


class LLExpSetup(LLObject):
    def __init__(self):
        super(LLExpSetup,self).__init__()

        self.p_mw_control_lines = []
        self.add_parameter('p_mw_control_lines',label="Microwave Control Lines",ptype=LLObjectParameter.PTYPE_LLOBJECT_LIST)

    def addControlLine(self,mw_control_line):
        self.p_mw_control_lines.append(mw_control_line)

