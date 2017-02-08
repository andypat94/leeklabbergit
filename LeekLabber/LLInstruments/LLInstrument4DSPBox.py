from LeekLabber import *
import numpy as np

class LLInstrument4DSPBox(LLInstrument):
    def __init__(self):
        super(LLInstrument4DSPBox,self).__init__()

        ## Define parameters locally ##
        self.p_rep_time = 200.0e-6 # Repetition rate of experiment
        self.p_num_averages = 10000 # Number of times to average response in hardware
        self.p_slow_dac_data = np.zeros(shape=(8,100000),dtype='double') #8 channels x 100us memory @ 1GS/s
        self.p_fast_dac_data = np.zeros(shape=(8,200000),dtype='double') #8 channels x 100us memory @ 2GS/s
        self.p_adc_data = np.zeros(shape=(8,100000),dtype='double') # 8 channels x 100us memory @ 1GS/s
        self.p_slow_t = np.linspace(0.,100.0e-6-1.0e-9, 100000) # Time values to go along with the slow_dac_data
        self.p_fast_t = np.linspace(0.,100.0e-6-0.5e-9, 100000) # Time values to go along with the fast_dac_data

        self.add_parameter('p_rep_time', label='Repetition Time', unit='s')
        self.add_parameter('p_num_averages', label='Averages')
        self.add_parameter('p_slow_dac_data', label='1GS DAC Data', unit='V', xvals='p_slow_t', xunit='s', xlabel='Time')
        self.add_parameter('p_fast_dac_data', label='2GS DAC Data', unit='V', xvals='p_fast_t', xunit='s', xlabel='Time')
        self.add_parameter('p_adc_data', label='ADC Data', unit='V', xvals='p_slow_t', xunit='s', xlabel='Time')


