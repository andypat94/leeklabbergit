from LeekLabber import *
import LeekLabber as LL
import numpy as np

class LLMicrowaveControlLine(LLObject):
    def __init__(self, exp_setup=None, NDrives=2, NReadouts=1):

        self.MEAS_IF_WINDOW = 500.0e6 # Hz
        self.DRIV_IF_WINDOW = 1000.0e6
        self.POWER_WINDOW = 20. # dBm
        self.FREQ_TOLERANCE = 1e3 # 1kHz tolerance

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

    def add_mwcl_refs(self):
        for dev in self.p_devices:
            dev.add_mwcl_ref(self)

    def select_drive(self, pulse):
        if pulse.measured:
            first_list = self.mapped_pulsed_measured_drives
            second_list = self.mapped_pulsed_unmeasured_drives
        else:
            second_list = self.mapped_pulsed_measured_drives
            first_list = self.mapped_pulsed_unmeasured_drives

        def test_drives(pulse, drives):
            for drive in drives:
                if (pulse.freq >= drive.minfreq
                        and pulse.freq <= drive.maxfreq
                        and pulse.power <= drive.power
                        and pulse.power >= drive.power - self.POWER_WINDOW ):
                    return drive
            return None

        selected_drive = test_drives(pulse, first_list)
        if selected_drive is None:
            selected_drive = test_drives(pulse, second_list)
        if selected_drive is None:
            print("A pulse could not find a driver.")
        return selected_drive

    def get_timebase(self, time, freq, power, measured):
        #todo: don't just make the array, grab it from a premade one?
        guess_drive = self.select_drive(LLPulseHelper(time=time, t=None, DC_I=None, DC_Q=None, freq=freq, power=power, device=None,measured=measured,basis_phase=0.0))
        dt = guess_drive.timestep
        N = int((time+0.5*dt)/dt)
        return np.linspace(start=0.0,stop=time,num=N,endpoint=False)

    def clear_needed_mw_drives(self):
        self.needed_mw_drives = []

    def clear_pulses(self):
        self.submitted_pulses = []

    def prepare_microwave_drive(self, freq, power, pulsed, measured, device):
        self.needed_mw_drives.append(LLMicrowaveDriveHelper(freq, power, pulsed, measured, device))
        self.ll_parent.prepare_microwave_drive(freq,power,pulsed, measured,device,self)

    #todo: would be cool if get_timeslot returned a pulse helper object that could then be later submitted with the envelope info.
    def submit_pulse(self, pulse_helper_obj):
        self.submitted_pulses.append(pulse_helper_obj)

    def plan_experiment(self):
        print("drive mapping started..")

        # TODO: implement even better planning algorithm

        MEAS_IF_WINDOW = self.MEAS_IF_WINDOW
        DRIV_IF_WINDOW = self.DRIV_IF_WINDOW
        POWER_WINDOW = self.POWER_WINDOW

        def clone_drives(drives):
            tmp = []
            for d in drives:
                tmp.append(LLMicrowaveDriveHelper(d.freq,d.power,d.pulsed,d.measured,d.device))
            return tmp
        def select_pulsed(drives,pulsed):
            return [drive for drive in drives if drive.pulsed == pulsed]
        def select_measured(drives,measured):
            return [drive for drive in drives if drive.measured == measured]

        # sort the requested drives out
        ds = clone_drives(self.needed_mw_drives)

        m_ds = select_measured(ds,True)
        um_ds = select_measured(ds,False)

        p_m_ds = select_pulsed(m_ds,True)
        c_m_ds = select_pulsed(m_ds,False)
        p_um_ds = select_pulsed(um_ds,True)
        c_um_ds = select_pulsed(um_ds,False)

        # group requests that fit into a nice if window (better algorithms for this almost certainly exist)

        def find_closest_drives(drives,powerwindow):
            min_distance =  1.0e20 # just use a very large number (no frequencys near this)
            min_i = -1
            min_j = -1
            N = len(drives)
            for i in range(0, N):
                for j in range(i+1, N):
                    distance = drives[i].distance_to(drives[j])
                    if distance<min_distance:
                        # ADDITIONAL CONSTRAINT on power closeness!!
                        if abs(drives[i].power - drives[j].power)<powerwindow:
                            min_distance = distance
                            min_i = i
                            min_j = j
                            if(min_distance < self.FREQ_TOLERANCE): #provides a huge speedup when dealing with many pulses at the same frequencies
                                return (min_distance, min_i, min_j)
            return (min_distance,min_i,min_j)

        def group_drives(drives,window,powerwindow):
            loop = True
            while(loop):
                result = find_closest_drives(drives,powerwindow)
                if(result[0]<window):
                    drives[result[1]].absorb(drives[result[2]])
                    del drives[result[2]]
                else:
                    loop = False

        ## FIRST LETS JUST TRY COMBINING UP PULSED DRIVES
        group_drives(p_m_ds, MEAS_IF_WINDOW, POWER_WINDOW)
        group_drives(p_um_ds, DRIV_IF_WINDOW, POWER_WINDOW)

        num_readout_gens = len(p_m_ds) + len(c_m_ds)
        num_control_gens = len(p_m_ds) + len(c_m_ds) + len(p_um_ds) + len(c_um_ds)

        combine_continuous_drives = False
        failed = False
        combine_all = False

        if(num_readout_gens <= self.p_n_readouts and num_control_gens <= self.p_n_drives):
            # we're good!
            all_ds = (p_m_ds, p_um_ds, c_m_ds, c_um_ds)
        else:
            combine_continuous_drives = True
            ds = clone_drives(self.needed_mw_drives)
            m_ds = select_measured(ds,True)
            um_ds = select_measured(ds,False)
            all_ds = (m_ds, um_ds)

        if(combine_continuous_drives):
            group_drives(m_ds, MEAS_IF_WINDOW, POWER_WINDOW)
            group_drives(um_ds, DRIV_IF_WINDOW, POWER_WINDOW)

            num_readout_gens = len(m_ds)
            num_control_gens = len(m_ds) +  len(um_ds)

            if(num_readout_gens <= self.p_n_readouts and num_control_gens <= self.p_n_drives):
                # we're good!
                combine_all = False
            else:
                combine_all = True

            if(combine_all):
                ds = clone_drives(self.needed_mw_drives)
                all_ds = ( ds,)

                group_drives(ds, MEAS_IF_WINDOW, POWER_WINDOW)

                num_readout_gens = len([drive for drive in ds if drive.measured])
                num_control_gens = len(ds)

                if (num_readout_gens <= self.p_n_readouts and num_control_gens <= self.p_n_drives):
                    # we're good!
                    pass
                else:
                    failed = True

        if failed:
            print("Failed to map drives to experimental setup")
            return
        else:
            if combine_all:
                print("Measurement and control drives have been mixed to enable drive mapping")
            if combine_continuous_drives:
                print("Continuous drives may be generated using upconversion to enable drive mapping")

        print("Drive mapping completed. Results:")

        self.mapped_mw_ds = []
        for d in all_ds:
            self.mapped_mw_ds += d

        id = 0

        for drive in self.mapped_mw_ds:
            if drive.measured:
                drive.choose_lo_frequency(MEAS_IF_WINDOW)
                drive.drive_id = id
                drive.readout_id = id
                drive.drive_generator = self.p_drive_gens[id]
                drive.readout_generator = self.p_readout_gens[id]
                id += 1

        for drive in self.mapped_mw_ds:
            if not drive.measured:
                drive.choose_lo_frequency(DRIV_IF_WINDOW)
                drive.drive_id = id
                drive.drive_generator = self.p_drive_gens[id]
                id += 1

        for drive in self.mapped_mw_ds:
            drive.dac_link(self.p_dac_data,self.p_dac_channel_i,self.p_dac_channel_q)

        for drive in self.mapped_mw_ds:
            drive.print_summary()

        self.mapped_pulsed_drives = select_pulsed(self.mapped_mw_ds, True)
        self.mapped_pulsed_measured_drives = select_measured(self.mapped_pulsed_drives, True)
        self.mapped_pulsed_unmeasured_drives = select_measured(self.mapped_pulsed_drives, False)

    def process_pulses(self):
        print("Processing " + str(len(self.submitted_pulses)) + " pulses.")

        #todo: add cacheing of some of this stuff to improve speed
        for pulse in self.submitted_pulses:
            selected_drive = self.select_drive(pulse)
            pulse.drive = selected_drive
            if selected_drive is not None:
                pulse.start_N = int((pulse.start_time/pulse.drive.timestep)+0.5)
                pulse.length_N = len(pulse.t)
                pulse.end_N = pulse.start_N+pulse.length_N
                pulse.real_start_time =pulse.length_N * pulse.drive.timestep
                #time_error = pulse.length_N*pulse.drive.timestep-pulse.start_time

                pulse.drive_amp_scale = 10.0**((selected_drive.power-pulse.power)/20.0)
                pulse.if_freq = pulse.freq-selected_drive.lo_frequency
                pulse.initial_phase = 2.0*np.pi*pulse.if_freq*pulse.real_start_time - np.pi*pulse.basis_phase

                cosbp = pulse.drive_amp_scale*np.cos(pulse.initial_phase)
                sinbp = pulse.drive_amp_scale*np.sin(pulse.initial_phase)
                pulse.DC_I_B = cosbp*pulse.DC_I - sinbp*pulse.DC_Q
                pulse.DC_Q_B = sinbp*pulse.DC_I + cosbp*pulse.DC_Q

                cosift = np.cos(2.0*np.pi*pulse.if_freq*pulse.t)
                sinift = np.sin(2.0*np.pi*pulse.if_freq*pulse.t)
                pulse.AC_I = cosift*pulse.DC_I_B -sinift*pulse.DC_Q_B
                pulse.AC_Q = sinift*pulse.DC_I_B +cosift*pulse.DC_Q_B

    def commit_dac_data(self, experiment_length):
        # prepare memory
        for drive in self.mapped_pulsed_drives:
            # resize arrays if necessary, also ensures link to dac data is good for all drives
            drive.dac_link(self.p_dac_data,self.p_dac_channel_i,self.p_dac_channel_q)
            drive.dac_resize(experiment_length)
            drive.dac_link(self.p_dac_data, self.p_dac_channel_i, self.p_dac_channel_q)
            # zero the arrays
            drive.dac_data_i.fill(0.)
            drive.dac_data_q.fill(0.)
        # copy pulse data to memory
        for pulse in self.submitted_pulses:
            pulse.drive.dac_data_i[pulse.start_N:pulse.end_N] = pulse.AC_I
            pulse.drive.dac_data_q[pulse.start_N:pulse.end_N] = pulse.AC_Q
        # check to see if overlapping  pulses have caused an amplitude > 1.0, change power to compensate
        for drive in self.mapped_pulsed_drives:
            max_i = np.abs(drive.dac_data_i).max()
            max_q = np.abs(drive.dac_data_q).max()
            if max_i>max_q:
                max = max_i
            else:
                max = max_q
            if max>1.0:
                drive.dac_data_i = drive.dac_data_i/max
                drive.dac_data_q = drive.dac_data_q/max
                drive.power = drive.power + 20.0*np.log10(max)


class LLMicrowaveDriveHelper:
    def __init__(self,freq,power,pulsed,measured,device):
        self.freq = freq
        self.power = power
        self.pulsed = pulsed
        self.measured = measured
        self.device = device

        self.minfreq = freq
        self.maxfreq = freq
        self.frequencies = [freq,]
        self.devices = [device,]

        self.lo_frequency = 0.
        self.readout_id = -1
        self.drive_id = -1
        self.readout_generator = None
        self.drive_generator = None

        self.timestep=0.0


    def absorb(self, another):
        if another.maxfreq>self.maxfreq:
            self.maxfreq = another.maxfreq
        if another.minfreq<self.minfreq:
            self.minfreq = another.minfreq

        self.devices += another.devices
        self.frequencies += another.frequencies

        if another.power > self.power: #keep track of highest power only
            self.power = another.power

        self.pulsed = True # combining two continuous drives will still require upconversion
        self.measured = self.measured or another.measured

    def distance_to(self, another):
        # returns the size of the window you'd get if you combined these
        selfBiggestMax = (self.maxfreq>=another.maxfreq)
        selfSmallestMin = (self.minfreq<=another.minfreq)
        if selfBiggestMax:
            if selfSmallestMin:
                #have total overlap
                window = self.maxfreq - self.minfreq
            else:
                window = self.maxfreq - another.minfreq
        else:
            if selfSmallestMin:
                # gap is negative when there is an overlap
                window = another.maxfreq - self.minfreq
            else:
                #have total overlap
                window  = another.maxfreq - another.minfreq
        return window

    def choose_lo_frequency(self, ifwindow):
        # TODO: could definitely choose this more intelligently
        if(self.pulsed):
            span = self.maxfreq - self.minfreq
            print span, ifwindow*0.4
            if(span < ifwindow * 0.4):
                self.lo_frequency =  (self.maxfreq + self.minfreq)/2. - 0.25 * ifwindow
            elif(span < ifwindow * 0.9):
                self.lo_frequency = (self.maxfreq + self.minfreq)/2. - 0.05 * ifwindow
            else:
                self.lo_frequency = (self.maxfreq + self.minfreq)/2.
        else:
            self.lo_frequency = self.maxfreq


    def print_summary(self):
        print("LO: " + str(self.lo_frequency))
        print("POW:" + str(self.power))
        print("RF Generator:" + str(self.drive_generator["Instrument Name"]))
        if self.readout_generator is not None:
            print("RF Generator:" + str(self.readout_generator["Instrument Name"]))
        print("    IF: " + str(self.frequencies[0]-self.lo_frequency))
        for i in range(1,len(self.frequencies)):
            print("        " + str(self.frequencies[i]-self.lo_frequency))

    def dac_link(self, p_dac_data, p_dac_channel_i, p_dac_channel_q):
        self.dac_data = p_dac_data[self.drive_id]  # dac_data is an LLObjectParameter
        self.dac_data_index_i = p_dac_channel_i[self.drive_id]
        self.dac_data_index_q = p_dac_channel_q[self.drive_id]
        self.dac_data_i = self.dac_data.get_value()[self.dac_data_index_i]
        self.dac_data_q = self.dac_data.get_value()[self.dac_data_index_q]
        self.tvals = self.dac_data.get_xvals()
        self.timestep = self.tvals[1] - self.tvals[0]

    def dac_resize(self, time):
        samples =  int((time/self.timestep)+0.5)
        oldref = self.dac_data.get_value()
        shape = oldref.shape
        if shape[-1] != samples:
            shape = list(shape)
            shape[-1] = samples
            self.dac_data.set_value(np.resize(oldref, shape))
            t = np.linspace(start=0.0, stop=time, num=samples, endpoint=False)
            self.dac_data.set_xvals(t)

class LLPulseHelper():
    def __init__(self, time, t, DC_I, DC_Q, freq, power,device,measured,basis_phase):

        self.start_time = time
        self.t = t
        self.DC_I = DC_I
        self.DC_Q = DC_Q
        self.freq = freq
        self.power = power
        self.device = device
        self.measured = measured
        self.basis_phase = 0.0

        self.drive = None
        self.drive_amp_scale = 1.0
        self.if_freq = 0.

class LLPulse(LLObject):
    def __init__(self):
        self.p_start_time = 0.0
        self.p_tvals = None
        self.p_dc_i = None
        self.p_dc_q = None
        self.p_freq = 0.
        self.p_power = 0.
        self.p_measured = False
        self.p_basis_phase = 0.
        self.p_if_freq = 0.
        self.p_drive_amp_scale = 1.

        self.add_parameter('p_start_time',label="Start Time",unit='s')
        self.add_parameter('p_dc_i',label="DC I",unit='V',xvals='p_tvals',xunit='s',ptype=LLObjectParameter.PTYPE_NUMPY)
        self.add_parameter('p_dc_q',label="DC Q",unit='V',xvals='p_tvals',xunit='s',ptype=LLObjectParameter.PTYPE_NUMPY)
        self.add_parameter('p_tvals',label="Time Values",unit='s',ptype=LLObjectParameter.PTYPE_NUMPY)
        self.add_parameter('p_freq',label="Absolute Frequency",unit='Hz')
        self.add_parameter('p_power',label="Power",unit='dBm')
        self.add_parameter('p_measured',label="Measure Response")
        self.add_parameter('p_basis_phase',label="Drive Basis Phase", unit='pi')
        self.add_parameter('p_if_freq',label="Intermediate Frequency", unit='Hz')

        self.drive = None
        self.drive_amp_scale = 1.0


class LLExpSetup(LLObject):
    def __init__(self):
        super(LLExpSetup,self).__init__(LL.LL_ROOT.expsetups)

        self.p_mwcls = []
        self.add_parameter('p_mwcls',label="Microwave Control Lines",ptype=LLObjectParameter.PTYPE_LLOBJECT_LIST)

    def prepare_microwave_drive(self, freq, power, pulsed, measured, device, mwcl):
        self.needed_mw_drives.append((freq,power,pulsed, measured,device,mwcl))

    def prepare_experiment(self):
        # Refresh the list of couplings and mwcls in all devices
        # TODO: In future it would be good to only do these things if they are really necessary?

        for dev in LL.LL_ROOT.devices.ll_children:
            dev.clear_coupling_refs()
            dev.clear_mwcl_refs()

        self.needed_mw_drives = [] # clear all microwave drives requested last time
        #self.submitted_pulses = [] # clear all pulses submitted last time

        for mwcl in self.p_mwcls:
            mwcl.clear_needed_mw_drives()
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

        for mwcl in self.p_mwcls:
            mwcl.process_pulses()

        for mwcl in self.p_mwcls:
            mwcl.commit_dac_data(experiment_length)

        # for mwcl in self.p_mwcls:
        #     mwcl.commit_gen_settings()
        #
        # for mwcl in self.p_mwcls:
        #     mwcl.retrieve_adc_data()