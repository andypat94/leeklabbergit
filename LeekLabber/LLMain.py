import LeekLabber as LL
from LeekLabber import *
from LeekLabber import LLInstruments, LLDevices, LLTasks
import PyQt5.QtCore as Qt

import PyQt5.QtWidgets as QtWidgets
import multiprocessing
import multiprocessing.reduction
from ctypes import *
from Queue import Full, Empty
from NamedMutex import NamedMutex
from mmap import mmap
from random import randrange

from timeit import default_timer as timer

LL.CONTROLLER = None

def start_leeklabber():
    Qt.pyqtRemoveInputHook() # we're handling threading/eventloops ourselves
    app = QtWidgets.QApplication([]) # create a Qt application

    # start a leeklabber control thread

    interface_creation_q = multiprocessing.Queue()
    control_thread = multiprocessing.Process(target=LLControllerThread,args=(interface_creation_q,))
    control_thread.start()

    #create interface to controller
    llci = LLControlInterface(interface_creation_q)

    # pass nothing but this interface to the gui thread
    tray = LL.LLQtSystemTray(llci)
    app.setQuitOnLastWindowClosed(False)
    app.exec_() #start the gui on this thread (necessary)


def LLControllerThread(interface_creation_q,*args,**kwargs):
    controller = LLController(interface_creation_q)
    controller.run_event_loop()

class LLController(object):
    def __init__(self, interface_creation_q):
        super(LLController, self).__init__()
        self.interface_creation_q = interface_creation_q
        self.connections = []
        LL.LL_ROOT = LL.LLRoot.from_blank()  # create a blank global root instance.

        self.add_test_system()

    def add_test_system(self):
        # Create Instruments
        i_SGS_QUBIT = LLInstruments.LLInstrumentRSSGS()
        i_SGS_QUBIT['Instrument Name'] = "Qubit Generator"
        i_SGS_QUBIT['Instrument Address'] = "192.168.1.20"
        i_SGS_RF = LLInstruments.LLInstrumentRSSGS()
        i_SGS_RF['Instrument Name'] = "RF Generator"
        i_SGS_RF['Instrument Address'] = "192.168.1.24"
        i_SGS_LO = LLInstruments.LLInstrumentRSSGS()
        i_SGS_LO['Instrument Name'] = "LO Generator"
        i_SGS_LO['Instrument Address'] = "192.168.1.26"
        i_FPGABOX = LLInstruments.LLInstrument4DSPBox()
        i_FPGABOX['Instrument Name'] = "4DSP FPGABOX"
        i_FPGABOX['Instrument Address'] = ""

        # Create Quantum Devices
        qd_Q1 = LLDevices.LLDeviceSimpleQubit()
        qd_Q1["Frequency"] = 6.0e9
        qd_R1 = LLDevices.LLDeviceSimpleResonator()
        qd_R1["Frequency"] = 9.0e9

        # Assign couplings between devices
        LLDeviceCoupling(qd_Q1, qd_R1, 10.0e6, 'Chi')

        # Create an Experimental Setup
        exp_setup = LLExpSetup()

        # Create a control line for the setup
        mwcl = LLMicrowaveControlLine(exp_setup)
        p_1gs_dac_data = i_FPGABOX.get_parameter("1GS DAC Data")
        p_2gs_dac_data = i_FPGABOX.get_parameter("2GS DAC Data")
        p_adc_data = i_FPGABOX.get_parameter("ADC Data")
        # First drive (for resonator) from 1gs first board
        drive = LLDrive(mwcl)
        drive["Drive Generator"] = i_SGS_RF
        drive["DAC Data"] = p_1gs_dac_data
        drive["DAC I Channel"] = 0
        drive["DAC Q Channel"] = 1
        drive["Readout Generator"] = i_SGS_LO
        drive["ADC Data"] = p_adc_data
        drive["ADC I Channel"] = 0
        drive["ADC Q Channel"] = 1
        # Second drive (for qubit) from 2gs first board
        drive = LLDrive(mwcl)
        drive["Drive Generator"] = i_SGS_QUBIT
        drive["DAC Data"] = p_2gs_dac_data
        drive["DAC I Channel"] = 0
        drive["DAC Q Channel"] = 1
        # This line is for measuring the resonator and controlling the qubit
        mwcl["Connected Devices"] += [qd_Q1, qd_R1]

        # Prepare an experiment with a single qubit rotation
        gate = LLTasks.LLTaskSingleQRotation(LL.LL_ROOT.task)
        gate["Qubit Device"] = qd_Q1  # qubit 1
        gate["Rotation Axis"] = 'X'  # drive on X
        gate["Rotation Angle"] = 0.5  # pi pulse

        gate2 = LLTasks.LLTaskDelay(LL.LL_ROOT.task)
        gate2["Delay Time"] = 1e-6
        gate2["Task Dependences"] = [gate, ]

        gate3 = LLTasks.LLTaskSingleQRotation(LL.LL_ROOT.task)
        gate3["Qubit Device"] = qd_Q1  # qubit 1
        gate3["Rotation Axis"] = 'X'  # drive on X
        gate3["Rotation Angle"] = 0.5  # pi pulse
        gate3["Task Dependences"] = [gate2, ]

        # large number of gates test
        prevGate = gate3
        for i in range(100):
            nextGate = LLTasks.LLTaskDelay(LL.LL_ROOT.task)
            nextGate["Delay Time"] = np.random.randint(1000)*1.0e-9
            nextGate["Task Dependences"] = [gate3,]
            prevGate=nextGate

            nextGate = LLTasks.LLTaskSingleQRotation(LL.LL_ROOT.task)
            nextGate["Qubit Device"] = qd_Q1  # qubit 1
            nextGate["Rotation Axis"] = 'X'  # drive on X
            nextGate["Rotation Angle"] = 0.5  # pi pulse
            nextGate["Task Dependences"] = [prevGate, ]
            prevGate=nextGate


        LL.LL_ROOT.task.create_or_update_subtasks_internal()
        LL.LL_ROOT.task.execute()  # do it!

    def run_event_loop(self):
        first = True
        while True:
            # check the interface creation queue to connect to interfaces on other processes as needed
            try:
                q_val = self.interface_creation_q.get_nowait()
                pipe = multiprocessing.reduction.rebuild_pipe_connection(*q_val[1])
                self.connections.append(LLControlConnection(pipe))
            except Empty:
                pass

            # allow all connections to process messages from their interfaces thread
            for conn in self.connections:
                conn.check_pipe()

            if first:
                if len(self.connections)>0:
                    self.share_system_state() # won't call this from the loop, will call this after significant state changes
                    first = False

    def share_system_state(self):
        length = sizeof(c_int)
        length += LL.LL_ROOT.binaryshare_set_location_get_length(length)
        print("Binarised root is " + str(length)+ " bytes.")

        for conn in self.connections:
            conn.share_system_state()


class LLControlConnection(object):
    def __init__(self, interface_pipe):
        self.interface_pipe = interface_pipe
        self.state_share_bufA = None
        self.state_share_bufB = None
        self.state_sharing = False

    def check_pipe(self):
        try:

            while self.interface_pipe.poll():
                p_val = self.interface_pipe.recv()
                if p_val[0]==LLControlInterface.cmd_state_sharing:
                    self.enable_system_state_share(sharing_enabled=p_val[1], mmap_name=p_val[2], mmap_size=p_val[3], mutex_name=p_val[4])
                elif p_val[0]==LLControlInterface.cmd_state_pipe:
                    self.state_pipe = multiprocessing.reduction.rebuild_pipe_connection(*p_val[1][1])

        except IOError:
            raise Exception("ControllerInterface connection closed")

    def enable_system_state_share(self, sharing_enabled, mmap_name, mmap_size, mutex_name):
        self.state_sharing = sharing_enabled
        self.state_mmap_name = mmap_name
        self.state_mmap_size = mmap_size
        self.state_mutex_name =  mutex_name

        self.state_mutex = (NamedMutex(self.state_mutex_name + 'A'), NamedMutex(self.state_mutex_name + 'B'))
        self.state_mmap = (mmap(-1, self.state_mmap_size, self.state_mmap_name + 'A'),
                           mmap(-1, self.state_mmap_size, self.state_mmap_name + 'B'))

    def share_system_state(self):
        start = timer()
        # grab access to one of the buffers. only in exceptional circumstances will it find both to be busy.. (other process only uses one at a time)
        if self.state_mutex[0].acquire(0): # try to acquire mutex 0
            mutexid = 0
        elif self.state_mutex[1].acquire(): # try to acquire mutex 1 for as long as it takes
            mutexid = 1
        else:
            print("Mutex lock failed")
            return

        # a mutex is locked. we can safely dump the data into the shared memory
        dump_buf = c_void_p.from_buffer(self.state_mmap[mutexid])

        LL.LL_ROOT.binaryshare_dump(addressof(dump_buf))

        # release the mutex so the other process can access the data
        self.state_mutex[mutexid].release()
        stop = timer()
        time = stop-start
        print("Dumped in " + str(time))


class LLControlInterface(object):
    cmd_state_sharing = 1
    cmd_state_pipe = 2

    def __init__(self, interface_creation_q):
        super(LLControlInterface,self).__init__()
        self.interface_creation_q = interface_creation_q
        self.control_pipe =  self.connect_to_controller()
        self.state_sharing = False

    def connect_to_controller(self):
        local_pipe, remote_pipe = multiprocessing.Pipe()
        self.control_pipe = local_pipe
        try:
            self.interface_creation_q.put(multiprocessing.reduction.reduce_connection(remote_pipe))
        except Full:
            pass
        return local_pipe

    def enable_system_state_share(self, bufsize=128*2**20): # default 128 MB buffer
        if self.state_sharing:
            return
        self.state_sharing = True

        self.state_id = str(randrange(1024*1024))
        self.state_mmap_size = bufsize
        self.state_mmap_name = "llab_mmap_state_id"+self.state_id
        self.state_mutex_name = "llab_mutex_state_id"+self.state_id

        self.state_mutex = (NamedMutex(self.state_mutex_name+'A'),NamedMutex(self.state_mutex_name+'B'))
        self.state_mmap = (mmap(-1, self.state_mmap_size, self.state_mmap_name+'A'),mmap(-1, self.state_mmap_size, self.state_mmap_name+'B'))

        self.control_pipe.send((self.cmd_state_sharing, True, self.state_mmap_name, self.state_mmap_size, self.state_mutex_name))

        local_pipe, remote_pipe = multiprocessing.Pipe()
        self.state_pipe = local_pipe
        self.control_pipe.send((self.cmd_state_pipe, multiprocessing.reduction.reduce_connection(remote_pipe)))
