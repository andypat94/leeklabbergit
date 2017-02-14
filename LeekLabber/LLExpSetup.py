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

    def add_mwcl_refs(self):
        for dev in self.p_devices:
            dev.add_mwcl_ref(self)

    def get_timebase(self, time, freq, power):
        # needs to have an idea of which devices are using which timebase already before pulses are submitted?
        return np.arange(1000.,dtype='double')

    def clear_needed_mw_drives(self):
        self.needed_mw_drives = []

    def prepare_microwave_drive(self, freq, power, pulsed, measured, device):
        self.needed_mw_drives.append(LLMicrowaveDriveHelper(freq, power, pulsed, measured, device))
        self.ll_parent.prepare_microwave_drive(freq,power,pulsed, measured,device,self)

    def submit_pulse(self, DC_I, DC_Q, freq, device):
        self.ll_parent.submit_pulse(DC_I,DC_Q,freq, device, self)

    def plan_experiment(self):
        # TODO: implement even better planning algorithm

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

        IF_WINDOW = 500.0e6 # Hz
        POWER_WINDOW = 20. # dBm

        ## FIRST LETS JUST TRY COMBINING UP PULSED DRIVES
        for drives in (p_m_ds, p_um_ds):
            group_drives(drives, IF_WINDOW, POWER_WINDOW)

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
            for drives in (m_ds, um_ds):
                group_drives(drives, IF_WINDOW, POWER_WINDOW)

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

                group_drives(ds, IF_WINDOW, POWER_WINDOW)

                num_readout_gens = len([drive for drive in ds if drive.measured])
                num_control_gens = len(ds)

                if (num_readout_gens <= self.p_n_readouts and num_control_gens <= self.p_n_drives):
                    # we're good!
                    pass
                else:
                    failed = True

        if failed:
            print("Failed to map drives to experimental setup")
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
                drive.choose_lo_frequency(IF_WINDOW)
                drive.drive_id = id
                drive.readout_id = id
                drive.drive_generator = self.p_drive_gens[id]
                drive.readout_generator = self.p_readout_gens[id]
                id += 1

        for drive in self.mapped_mw_ds:
            if not drive.measured:
                drive.choose_lo_frequency(IF_WINDOW)
                drive.drive_id = id
                drive.drive_generator = self.p_drive_gens[id]
                id += 1

        for drive in self.mapped_mw_ds:
            drive.print_summary()

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

class LLExpSetup(LLObject):
    def __init__(self):
        super(LLExpSetup,self).__init__(LL.LL_ROOT.expsetups)

        self.p_mwcls = []
        self.add_parameter('p_mwcls',label="Microwave Control Lines",ptype=LLObjectParameter.PTYPE_LLOBJECT_LIST)

    def prepare_microwave_drive(self, freq, power, pulsed, measured, device, mwcl):
        self.needed_mw_drives.append((freq,power,pulsed, measured,device,mwcl))

    def submit_pulse(self, DC_I, DC_Q, freq, device, line):
        self.submitted_pulses.append((DC_I, DC_Q, freq, device, line))

    def prepare_experiment(self):
        # Refresh the list of couplings and mwcls in all devices
        # TODO: In future it would be good to only do these things if they are really necessary?

        for dev in LL.LL_ROOT.devices.ll_children:
            dev.clear_coupling_refs()
            dev.clear_mwcl_refs()

        self.needed_mw_drives = [] # clear all microwave drives requested last time
        self.submitted_pulses = [] # clear all pulses submitted last time

        for mwcl in self.p_mwcls:
            mwcl.clear_needed_mw_drives()
            #mwcl.clear_pulses()

        for cp in LL.LL_ROOT.couplings.ll_children:
            cp.add_coupling_refs() #gives all devices a reference to any couplings associated with them

        for mwcl in self.p_mwcls:
            mwcl.add_mwcl_refs() #gives all devices a reference to any microwave control lines associated with them

        for dev in LL.LL_ROOT.devices.ll_children:
            dev.set_control_line()

    def plan_experiment(self):

        for mwcl in self.p_mwcls:
            mwcl.plan_experiment()

    def execute(self):
        print ("processing " + str(len(self.submitted_pulses)) + " submitted pulses.")