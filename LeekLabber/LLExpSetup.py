from LeekLabber import *
import LeekLabber as LL
import numpy as np

class LLMicrowaveControlLine(LLObject):
    def __init__(self, exp_setup=None, NDrives=2, NReadouts=1):
        super(LLMicrowaveControlLine, self).__init__(exp_setup)

        # Add local parameters
        self.p_n_drives = NDrives
        self.p_n_readouts = NReadouts
        self.p_dac_data = [None]*NDrives
        self.p_adc_data = [None]*NReadouts
        self.p_drive_gens = [None]*NDrives
        self.p_readout_gens = [None]*NReadouts
        self.p_dac_channel_i = np.arange(self.p_n_drives,dtype='int')
        self.p_dac_channel_q = np.arange(self.p_n_drives,dtype='int')
        self.p_adc_channel_i = np.arange(self.p_n_readouts,dtype='int')
        self.p_adc_channel_q = np.arange(self.p_n_readouts,dtype='int')
        self.p_s21_not_s11 = True
        self.p_devices = []
        self.prev_devices = []

        # Register parameters
        self.add_parameter('p_n_drives',label="Number of Drives",onChange=self.resize_lists)
        self.add_parameter('p_n_readouts',label="Number of Readouts",onChange=self.resize_lists)
        self.add_parameter('p_dac_data',label='DACs for Drives',ptype=LLObjectParameter.PTYPE_LLPARAMETER_LIST)
        self.add_parameter('p_dac_channel_i',label="DAC Channel I",)
        self.add_parameter('p_dac_channel_q',label="DAC Channel Q")
        self.add_parameter('p_adc_data',label='ADCs for Readouts',ptype=LLObjectParameter.PTYPE_LLPARAMETER_LIST)
        self.add_parameter('p_adc_channel_i',label="ADC Channel I")
        self.add_parameter('p_adc_channel_q',label="ADC Channel Q")
        self.add_parameter('p_s21_not_s11', label="Transmission (Not Reflection)")
        self.add_parameter('p_devices', label="Connected Devices",ptype=LLObjectParameter.PTYPE_LLOBJECT_LIST)
        self.add_parameter('p_drive_gens',label="Drive Generators",ptype=LLObjectParameter.PTYPE_LLOBJECT_LIST)
        self.add_parameter('p_readout_gens',label="Readout Generators",ptype=LLObjectParameter.PTYPE_LLOBJECT_LIST)

    def resize_lists(self):
        def resize(lst,n):
            return lst[0:n]+[None]*(n-len(lst))
        self.p_dac_channel_i.resize(self.p_n_drives)
        self.p_dac_channel_q.resize(self.p_n_drives)
        self.p_adc_channel_i.resize(self.p_n_readouts)
        self.p_adc_channel_q.resize(self.p_n_readouts)
        self.p_dac_data = resize(self.p_dac_data,self.p_n_drives)
        self.p_adc_data = resize(self.p_adc_data,self.p_n_readouts)
        self.p_drive_gens = resize(self.p_drive_gens,self.p_n_drives)
        self.p_readout_gens = resize(self.p_readout_gens,self.p_n_readouts)

    def set_parent(self, parent):
        if parent != self.ll_parent:
            if parent is None:
                pass
            else:
                parent["Microwave Control Lines"] += [self,]
            if self.ll_parent is None:
                pass
            else:
                self.ll_parent["Microwave Control Lines"] = [mwcl for mwcl in self.ll_parent["Microwave Control Lines"] if mwcl!= self]
        retval = super(LLMicrowaveControlLine, self).set_parent(parent)
        return retval

class LLExpSetup(LLObject):
    def __init__(self):
        super(LLExpSetup,self).__init__(LL.LL_ROOT.expsetups)

        self.p_mw_control_lines = []
        self.add_parameter('p_mw_control_lines',label="Microwave Control Lines",ptype=LLObjectParameter.PTYPE_LLOBJECT_LIST)

