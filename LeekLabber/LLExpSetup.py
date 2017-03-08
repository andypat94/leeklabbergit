from LeekLabber import *
import LeekLabber as LL
import numpy as np

class LLMicrowaveControlLine(LLObject):
    def __init__(self, exp_setup=None, NDrives=2, NReadouts=1):
        super(LLMicrowaveControlLine, self).__init__(exp_setup)

        self.p_devices = []
        self.p_drives = []
        self.add_parameter('p_devices', label="Connected Devices", ptype=LLObjectParameter.PTYPE_LLOBJECT_LIST)
        self.add_parameter('p_drives', label="Microwave Drives", ptype=LLObjectParameter.PTYPE_LLOBJECT_LIST)
        self.pulses = []

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

    def add_mwcl_refs(self):
        for dev in self.p_devices:
            dev.add_mwcl_ref(self)

    def clear_pulses(self):
        del self.pulses[:]

    def prepare_pulse(self,pulse):
        self.pulses.append(pulse)

    def plan_experiment(self):
        print("Control line must be prepared for " + str(len(self.pulses)) + " pulses.")

        #todo: this planning algorithm is far from perfect

        # check if existing plan already works
        fail = False
        for pulse in self.pulses:
            if not pulse.check_drive():
                fail = True
                break

        if fail: #replan if necessary

            for drive in self.p_drives:
                drive.clear_plan()

            for pulse in self.pulses:
                pulse.clear_plan()

            planned_pulses=0

            # First we place the modulated, measured pulses
            for pulse in self.pulses:
                if pulse.p_measured and pulse.p_pulsed:
                    for drive in self.p_drives:
                        if drive.try_pulse(pulse):
                            planned_pulses += 1
                            break
            # Next we place the unmodulated, measured pulses
            for pulse in self.pulses:
                if pulse.p_measured and (not pulse.p_pulsed):
                    for drive in self.p_drives:
                        if drive.try_pulse(pulse):
                            planned_pulses += 1
                            break
            # Next we place the modulated, unmeasured pulses
            for pulse in self.pulses:
                if (not pulse.p_measured) and pulse.p_pulsed:
                    for drive in self.p_drives:
                        if drive.try_pulse(pulse):
                            planned_pulses += 1
                            break
            # Finally place unmodulated, unmeasured pulses
            for pulse in self.pulses:
                if (not pulse.p_measured) and (not pulse.p_pulsed):
                    for drive in self.p_drives:
                        if drive.try_pulse(pulse):
                            planned_pulses += 1
                            break

            # Place unmodulated pulses in modulated slots if necessary
            if planned_pulses < len(self.pulses):
                for pulse in self.pulses:
                    if not pulse.planned:
                        for drive in self.p_drives:
                            if drive.try_pulse(pulse, True):
                                planned_pulses += 1
                                break

            # Give up
            if planned_pulses < len(self.pulses):
                print("Pulse planning failed.")

            for drive in self.p_drives:
                drive.finalize_plan()
                drive.print_summary()

    def execute(self, experiment_length):
        for drive in self.p_drives:
            drive.execute(experiment_length)

class LLDrive(LLObject):
    def __init__(self, mwcl=None):
        super(LLDrive, self).__init__(mwcl)

        self.p_pulsed_capable = False
        self.p_readout_capable = False

        self.p_drive_generator = None
        self.p_readout_generator = None

        self.p_dac_data = None
        self.p_adc_data = None

        self.p_dac_ch_num_i = 0
        self.p_dac_ch_num_q = 0
        self.p_adc_ch_num_i = 0
        self.p_adc_ch_num_q = 0

        self.p_min_freq = 0.0
        self.p_max_freq = 0.0
        self.p_min_power = 0.0
        self.p_max_power = 0.0

        self.add_parameter('p_pulsed_capable', label="Pulsed Capable")
        self.add_parameter('p_readout_capable', label="Readout Capable")
        self.add_parameter('p_drive_generator', label="Drive Generator", ptype=LLObjectParameter.PTYPE_LLOBJECT)
        self.add_parameter('p_readout_generator', label="Readout Generator", ptype=LLObjectParameter.PTYPE_LLOBJECT)
        self.add_parameter('p_dac_data', label="DAC Data", ptype=LLObjectParameter.PTYPE_LLPARAMETER,onChange=self.dac_added)
        self.add_parameter('p_adc_data', label="ADC Data", ptype=LLObjectParameter.PTYPE_LLPARAMETER,onChange=self.adc_added)
        self.add_parameter('p_dac_ch_num_i', label="DAC I Channel")
        self.add_parameter('p_dac_ch_num_q', label="DAC Q Channel")
        self.add_parameter('p_adc_ch_num_i', label="ADC I Channel")
        self.add_parameter('p_adc_ch_num_q', label="ADC Q Channel")

        self.dac_dt = 0.
        self.if_window = 0.
        self.power_window = 40.
        self.freq_res = 1.0e3
        self.max_t = 1.0e-3
        self.max_samples = 0
        self.t_vals = None

        self.planned = False
        self.plan_output = False
        self.plan_modulated = False
        self.plan_lo_frequency = 0.
        self.plan_power = 0.
        self.mod_required = False

        self.add_parameter('planned',label="Planned")
        self.add_parameter('plan_output',label="Plan Output")
        self.add_parameter('plan_modulated',label="Plan Modulated")
        self.add_parameter('plan_lo_frequency',label="Plan Frequency",unit='Hz')
        self.add_parameter('plan_power',label="Plan Power",unit='dBm')

        self.pulses = []

    def set_parent(self, parent):
        if parent != self.ll_parent:
            if parent is None:
                pass
            else:
                parent["Microwave Drives"] += [self,]
            if self.ll_parent is None:
                pass
            else:
                self.ll_parent["Microwave Drives"] = [mwcl for mwcl in self.ll_parent["Microwave Drives"] if mwcl!= self]
        retval = super(LLDrive, self).set_parent(parent)
        return retval

    def execute(self, experiment_length):
        if self.plan_modulated:
            # Connect to and resize dac data if necessary
            exp_len_n = int((experiment_length/self.dac_dt)+0.5)
            cur_shape = list(self.p_dac_data.get_value().shape)
            if cur_shape[-1] != exp_len_n:
                cur_shape[-1] = exp_len_n
                new_data = np.resize(self.p_dac_data.get_value(),cur_shape)
                self.p_dac_data.set_value(new_data)
                self.p_dac_data.set_xvals(self.t_vals[0:exp_len_n])
            t = self.p_dac_data.get_xvals()
            dac_i = self.p_dac_data.get_value()[self.p_dac_ch_num_i]
            dac_q = self.p_dac_data.get_value()[self.p_dac_ch_num_q]

            # Fill dac data
            dac_i.fill(0.)
            dac_q.fill(0.)
            for pulse in self.pulses:
                if pulse.p_pulsed:
                    dac_i[pulse.start_n:pulse.stop_n] += pulse.p_ac_i
                    dac_q[pulse.start_n:pulse.stop_n] += pulse.p_ac_q
                else:
                    # a continuous drive was assigned to a modulated line so create a continuous IF
                    dac_i += pulse.p_amp_scale*np.cos(2.0*np.pi*pulse.p_if_freq*t)
                    dac_q += pulse.p_amp_scale*np.sin(2.0*np.pi*pulse.p_if_freq*t)

            max = np.abs(dac_i).max()
            qmax = np.abs(dac_q).max()
            if(qmax>max):
                max = qmax
            if(max>1.0):
                dac_i /= max
                dac_q /= max
                extra_power = 20.*np.log10(max)
            else:
                extra_power = 0.
            extra_power = 0.
        else:
            extra_power = 0.

        # Configure the RF generators
        self.p_drive_generator["Frequency"] = self.plan_lo_frequency
        self.p_drive_generator["Power"] = self.plan_power + extra_power
        self.p_drive_generator["IQ Modulation"] = self.plan_modulated
        self.p_drive_generator["Output"] = self.plan_output

        if self.p_readout_generator is not None:
            self.p_readout_generator["Frequency"] = self.plan_lo_frequency
            self.p_readout_generator["Power"] = 16.0
            self.p_readout_generator["IQ Modulation"] = False
            self.p_readout_generator["Output"] = self.plan_output

    def get_timebase(self, pulse, start, length):
        pulse.start_n = int((start/self.dac_dt)+0.5)
        pulse.length_n =  int((length/self.dac_dt)+0.5)
        pulse.stop_n = pulse.start_n + pulse.length_n
        pulse.t_vals = self.t_vals[0:pulse.length_n]
        pulse.abs_t = self.t_vals[pulse.start_n:pulse.stop_n]

    def dac_added(self):
        if self.p_dac_data is None:
            self.p_pulsed_capable = False
            self.dac_dt = 0.
        else:
            tvals = self.p_dac_data.get_xvals()
            if len(tvals)>0:
                self.dac_dt = tvals[1]-tvals[0]
                self.if_window = 1.0/self.dac_dt
                self.max_samples = int((self.max_t/self.dac_dt)+0.5)
                self.t_vals = np.linspace(start=0.0, stop=self.max_t, num=self.max_samples, endpoint=False)
            self.p_pulsed_capable = True

    def adc_added(self):
        self.p_readout_capable = self.p_adc_data is not None

    def clear_plan(self):
        self.planned = False
        self.p_min_freq = 0.0
        self.p_max_freq = 0.0
        self.p_min_power = 0.0
        self.p_max_power = 0.0
        self.mod_required = False
        del self.pulses[:]

    def try_pulse(self, pulse, allow_continuous_modulation=False):
        if allow_continuous_modulation:
            if pulse.p_pulsed and not self.p_pulsed_capable:
                return False
        else:
            if pulse.p_pulsed != self.p_pulsed_capable:
                return False
        if pulse.p_measured and not self.p_readout_capable:
            return False
        if self.planned:
            if not self.p_pulsed_capable:
                return False
            # return true if the frequency and power fits the already planned values
            if pulse.p_frequency > self.p_max_freq:
                max_freq = pulse.p_frequency
                min_freq = self.p_min_freq
            elif pulse.p_frequency < self.p_min_freq:
                max_freq = self.p_max_freq
                min_freq = pulse.p_frequency
            else:
                max_freq = self.p_max_freq
                min_freq = self.p_min_freq

            if max_freq-min_freq > self.if_window:
                return False

            if pulse.p_power > self.p_max_power:
                max_power = pulse.p_power
                min_power = self.p_min_power
            elif pulse.p_power < self.p_min_power:
                max_power = self.p_max_power
                min_power = pulse.p_power
            else:
                max_power = self.p_max_power
                min_power = self.p_min_power

            if max_power-min_power > self.power_window:
                return False

            self.p_min_freq = min_freq
            self.p_max_freq = max_freq
            self.p_min_power = min_power
            self.p_max_power = max_power
            self.mod_required = self.mod_required or pulse.p_pulsed or (max_freq-min_freq)>self.freq_res

            pulse.set_drive(self)
            self.pulses.append(pulse)

            return True

        else:
            # set the current values and return true
            self.planned = True
            self.p_min_freq = pulse.p_frequency
            self.p_max_freq = pulse.p_frequency
            self.p_min_power = pulse.p_power
            self.p_max_power = pulse.p_power
            self.mod_required = pulse.p_pulsed

            pulse.set_drive(self)
            self.pulses.append(pulse)

            return True

    def finalize_plan(self):
        self.plan_output = self.planned
        self.plan_power = self.p_max_power
        self.plan_modulated = self.mod_required
        if self.plan_modulated :
            span = self.p_max_freq - self.p_min_freq
            if (span < self.if_window * 0.4):
                self.plan_lo_frequency = (self.p_max_freq + self.p_min_freq) / 2. - 0.25 * self.if_window
            elif (span < self.if_window * 0.9):
                self.plan_lo_frequency = (self.p_max_freq + self.p_min_freq) / 2.# - 0.05 * self.if_window
            else:
                self.plan_lo_frequency = (self.p_max_freq + self.p_min_freq) / 2.
        else:
            self.plan_lo_frequency = self.p_max_freq

        for pulse in self.pulses:
            pulse.p_if_freq = pulse.p_frequency - self.plan_lo_frequency
            pulse.p_amp_scale = 10.0**((pulse.p_power - self.plan_power)/20.0)

    def print_summary(self):
        print(self.plan_output, self.plan_lo_frequency, self.plan_power, self.plan_modulated, self.p_min_freq, self.p_max_freq)


class LLPulse(LLObject):
    def __init__(self):
        super(LLPulse,self).__init__(LL.LL_ROOT.pulses)

        #parameters set by preparation
        self.p_device = None
        self.p_frequency = 0.0
        self.p_power = 0.0
        self.p_pulsed = False
        self.p_measured = False

        #parameters set at planning
        self.p_if_freq = 0.0
        self.p_planned_drive = None
        self.p_amp_scale = 1.0

        #parameters set at submission
        self.p_start = 0.0
        self.p_length = 0.0
        self.p_dc_i = np.empty(0)
        self.p_dc_q = np.empty(0)
        self.p_ac_i = np.empty(0)
        self.p_ac_q = np.empty(0)
        self.p_basis_phase = 0.
        self.start_n = 0
        self.stop_n = 0
        self.length_n = 0
        self.t_vals = np.empty(0)
        self.abs_t = np.empty(0)
        self.p_bas_i = np.empty(0)
        self.p_bas_q = np.empty(0)

        self.add_parameter('p_frequency', label="Frequency",unit='Hz')
        self.add_parameter('p_power', label="Power",unit='dBm')
        self.add_parameter('p_pulsed', label="Pulsed")
        self.add_parameter('p_measured', label="Measured")
        self.add_parameter('p_if_freq', label="IF Frequency", unit='Hz')
        self.add_parameter('p_start', label="Start Time", unit='s')
        self.add_parameter('p_length', label="Length", unit='s')
        self.add_parameter('p_dc_i', label="DC I", unit='V')
        self.add_parameter('p_dc_q', label="DC Q", unit='V')
        self.add_parameter('p_basis_phase', label="Basis Phase", unit='pi')
        self.add_parameter('p_ac_i', label="AC I", unit='V')
        self.add_parameter('p_ac_q', label="AC Q", unit='V')

    def check_drive(self):
        if self.p_planned_drive is None:
            return False
        else:
            return False # todo: implement the check


    def clear_plan(self):
        self.planned = False

    def set_drive(self, drive):
        self.p_planned_drive = drive
        self.planned = True

    def prepare_pulse(self, device, frequency, power, pulsed, measured):
        self.p_device = device
        self.p_frequency = frequency
        self.p_power = power
        self.p_pulsed = pulsed
        self.p_measured = measured

        self.p_device.prepare_pulse(self)

    def get_timebase(self, start, length):
        self.p_start = start
        self.p_length = length
        if self.p_planned_drive is not None:
            self.p_planned_drive.get_timebase(self, start, length)
        return self.t_vals

    def submit_pulse(self, dc_i, dc_q, basis_phase):
        self.p_dc_i = dc_i
        self.p_dc_q = dc_q
        self.p_basis_phase = basis_phase

        # rotate BACKWARDS into the basis
        cosbp = self.p_amp_scale*np.cos(np.pi*basis_phase)
        sinbp = self.p_amp_scale*np.sin(np.pi*basis_phase)
        self.p_bas_i = cosbp*dc_i + sinbp*dc_q
        self.p_bas_q = -sinbp*dc_i + cosbp*dc_q

        # rotate FORWARDS into the rotating frame
        cosift = np.cos(2.0*np.pi*self.p_if_freq*self.abs_t)
        sinift = np.sin(2.0*np.pi*self.p_if_freq*self.abs_t)
        self.p_ac_i = cosift*self.p_bas_i - sinift*self.p_bas_q
        self.p_ac_q = sinift*self.p_bas_i + cosift*self.p_bas_q

class LLExpSetup(LLObject):
    def __init__(self):
        super(LLExpSetup,self).__init__(LL.LL_ROOT.expsetups)

        self.p_mwcls = []
        self.add_parameter('p_mwcls',label="Microwave Control Lines",ptype=LLObjectParameter.PTYPE_LLOBJECT_LIST)

    def update_coupling_refs(self):

        for dev in LL.LL_ROOT.devices.ll_children:
            dev.clear_coupling_refs()

        for cp in LL.LL_ROOT.couplings.ll_children:
            cp.add_coupling_refs() #gives all devices a reference to any couplings associated with them


    def prepare_experiment(self):
        # Refresh the list of couplings and mwcls in all devices
        # TODO: In future it would be good to only do these things if they are really necessary?

        for dev in LL.LL_ROOT.devices.ll_children:
            dev.clear_coupling_refs()
            dev.clear_mwcl_refs()
            dev.clear_state_vars()

        for mwcl in self.p_mwcls:
            mwcl.clear_pulses()

        for cp in LL.LL_ROOT.couplings.ll_children:
            cp.add_coupling_refs() #gives all devices a reference to any couplings associated with them

        for mwcl in self.p_mwcls:
            mwcl.add_mwcl_refs() #gives all devices a reference to any microwave control lines associated with them

        for dev in LL.LL_ROOT.devices.ll_children:
            dev.set_control_line()

    def plan_experiment(self):

        for mwcl in self.p_mwcls:
            mwcl.plan_experiment()

    def execute(self, experiment_length):

        # get control lines to set experiment params
        for mwcl in self.p_mwcls:
            mwcl.execute(experiment_length)

        # push params to devices
        for instrument in LL.LL_ROOT.instruments.ll_children:
            instrument.setup_internal()

        # todo: instruments should be prepared for readout, then something like trigger() events should be sent to anything that needs one in a correct order to start the experiment
        # for now, send every instrument a readout instruction
        for instrument in LL.LL_ROOT.instruments.ll_children:
            instrument.readout_internal()

        pass