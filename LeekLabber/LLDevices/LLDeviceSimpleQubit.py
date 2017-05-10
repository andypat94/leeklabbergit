from LeekLabber import *


class LLDeviceSimpleQubit(LLMicrowaveDevice):
    def __init__(self):
        super(LLDeviceSimpleQubit,self).__init__()

        ## Define parameters locally ##
        self.p_anharmonicity = 250.0e6
        self.p_t1 = 10.0e-6 # Qubit T1
        self.p_t2 = 12.0e-6 # Qubit T2

        ## Register these variables as parameters (these will be displayed in the GUI, stored in / restored by logs) ##
        self.add_parameter('p_anharmonicity', label='Anharmonicity', unit='Hz')
        self.add_parameter('p_t1', label='T1', unit='s')
        self.add_parameter('p_t2', label='T2', unit='s')

        self.p_calib_shape = 'Gaussian'
        self.p_calib_truncation = 0.0
        self.p_calib_transition = 0.0
        self.p_calib_power_pi = 0.0
        self.p_calib_width_pi = 0.0
        self.p_calib_power_pi2 = 0.0
        self.p_calib_width_pi2 = 0.0

        self.add_parameter('p_calib_shape', label="Calibrated Shape", value_dict={'Square':'Square','Gaussian':'Gaussian','Tanh':'Tanh','DRAG':'DRAG','hDRAG':'hDRAG'})
        self.add_parameter('p_calib_truncation', label="Calibrated Truncation", unit="width(s)")
        self.add_parameter('p_calib_transition', label="Calibrated Transition", unit="s")
        self.add_parameter('p_calib_power_pi', label="Calibrated Pi Power", unit="dBm")
        self.add_parameter('p_calib_width_pi', label="Calibrated Pi Width", unit="s")
        self.add_parameter('p_calib_power_pi2', label="Calibrated Pi/2 Power", unit="dBm")
        self.add_parameter('p_calib_width_pi2', label="Calibrated Pi/2 Width", unit="s")

        self.s_phi_offset = 0.0 # using s_ to signify a state machine variable

    def clear_state_vars(self):
        super(LLDeviceSimpleQubit,self).clear_state_vars()

        self.s_phi_offset = 0.0

