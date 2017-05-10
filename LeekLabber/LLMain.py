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
from time import sleep

import gc
import numpy as np

import sys
import traceback
import math
import re

import xml.etree.ElementTree as xmlet

from os  import  getpid

LL.CONTROLLER = None

def start_leeklabber():
    myappid = u'leeklab.leeklabber.leeklabber.0'  # arbitrary string
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

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
    print "Gui Thread %i" % getpid()
    app.exec_() #start the gui on this thread (necessary)



def LLControllerThread(interface_creation_q,*args,**kwargs):
    print "Controller Thread %i" % getpid()

    gc.disable() # cyclic references in this  control process will now stick around forever unless dealt with.. ok
    controller = LLController(interface_creation_q)
    try:
        controller.run_event_loop()
    except:
        print "Error in Control Thread"
        traceback.print_exc()
        #raise

class LLController(object):
    def __init__(self, interface_creation_q):
        super(LLController, self).__init__()
        self.interface_creation_q = interface_creation_q
        self.connections = []

        LL.LL_ROOT = LL.LLRoot.from_blank()  # create a blank global root instance.

    def add_test_system(self):

        # Create Instruments
        i_SGS_QUBIT2 = LLInstruments.LLInstrumentRSSGS()
        i_SGS_QUBIT2['Instrument Name'] = "Qubit Generator 2"
        i_SGS_QUBIT2['Instrument Address'] = "192.168.1.21"
        i_SGS_QUBIT_B2 = LLInstruments.LLInstrumentRSSGS()
        i_SGS_QUBIT_B2['Instrument Name'] = "Qubit Generator B 2"
        i_SGS_QUBIT_B2['Instrument Address'] = "192.168.1.23"
        i_SGS_RF2 = LLInstruments.LLInstrumentRSSGS()
        i_SGS_RF2['Instrument Name'] = "RF Generator 2"
        i_SGS_RF2['Instrument Address'] = "192.168.1.25"
        i_SGS_LO2 = LLInstruments.LLInstrumentRSSGS()
        i_SGS_LO2['Instrument Name'] = "LO Generator 2"
        i_SGS_LO2['Instrument Address'] = "192.168.1.27"
        i_SGS_QUBIT = LLInstruments.LLInstrumentRSSGS()
        i_SGS_QUBIT['Instrument Name'] = "Qubit Generator"
        i_SGS_QUBIT['Instrument Address'] = "192.168.1.20"
        i_SGS_QUBIT_B = LLInstruments.LLInstrumentRSSGS()
        i_SGS_QUBIT_B['Instrument Name'] = "Qubit Generator B"
        i_SGS_QUBIT_B['Instrument Address'] = "192.168.1.22"
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
        qd_Q1["Device Name"] = "Coaxmon A"
        qd_Q1["Frequency"] = 6.0e9
        qd_R1 = LLDevices.LLDeviceSimpleResonator()
        qd_R1["Device Name"] = "Resonator A"
        qd_R1["Frequency"] = 9.0e9
        qd_Q2 = LLDevices.LLDeviceSimpleQubit()
        qd_Q2["Device Name"] = "Coaxmon B"
        qd_Q2["Frequency"] = 7.0e9
        qd_R2 = LLDevices.LLDeviceSimpleResonator()
        qd_R2["Device Name"] = "Resonator B"
        qd_R2["Frequency"] = 10.0e9

        # Assign couplings between devices
        LLDeviceCoupling(qd_Q1, qd_R1, 10.0e6, '2Chi')
        LLDeviceCoupling(qd_Q2, qd_R2, 20.0e6, '2Chi')
        LLDeviceCoupling(qd_Q2, qd_R1, 1.0e6, '2Chi')

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
        # Third drive with no pulsing ability
        drive = LLDrive(mwcl)
        drive["Drive Generator"] = i_SGS_QUBIT_B
        drive["DAC Data"] = None
        # Second drive (for qubit) from 2gs first board
        drive = LLDrive(mwcl)
        drive["Drive Generator"] = i_SGS_QUBIT
        drive["DAC Data"] = p_2gs_dac_data
        drive["DAC I Channel"] = 0
        drive["DAC Q Channel"] = 1
        # This line is for measuring the resonator and controlling the qubit
        mwcl["Connected Devices"] += [qd_Q1, qd_R1]

        mwcl = LLMicrowaveControlLine(exp_setup)
        p_1gs_dac_data = i_FPGABOX.get_parameter("1GS DAC Data")
        p_2gs_dac_data = i_FPGABOX.get_parameter("2GS DAC Data")
        p_adc_data = i_FPGABOX.get_parameter("ADC Data")
        # First drive (for resonator) from 1gs first board
        drive = LLDrive(mwcl)
        drive["Drive Generator"] = i_SGS_RF2
        drive["DAC Data"] = p_1gs_dac_data
        drive["DAC I Channel"] = 2
        drive["DAC Q Channel"] = 3
        drive["Readout Generator"] = i_SGS_LO2
        drive["ADC Data"] = p_adc_data
        drive["ADC I Channel"] = 2
        drive["ADC Q Channel"] = 3
        # Third drive with no pulsing ability
        drive = LLDrive(mwcl)
        drive["Drive Generator"] = i_SGS_QUBIT_B2
        drive["DAC Data"] = None
        # Second drive (for qubit) from 2gs first board
        drive = LLDrive(mwcl)
        drive["Drive Generator"] = i_SGS_QUBIT2
        drive["DAC Data"] = p_2gs_dac_data
        drive["DAC I Channel"] = 2
        drive["DAC Q Channel"] = 3
        # This line is for measuring the resonator and controlling the qubit
        mwcl["Connected Devices"] += [qd_Q2, qd_R2]

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

        gate4 = LLTasks.LLTaskSingleQMeasure(LL.LL_ROOT.task)
        gate4["Qubit Device"] = qd_Q1  # qubit 1
        gate4["Task Dependences"] = [gate3, ]

        # large number of gates test
        # prevGate = gate3
        # for i in range(4):
        #
        #     nextGate = LLTasks.LLTaskDelay(LL.LL_ROOT.task)
        #     nextGate["Delay Time"] = np.random.randint(1000)*1.0e-9
        #     nextGate["Task Dependences"] = [gate3,]
        #     prevGate=nextGate
        #
        #     nextGate = LLTasks.LLTaskSingleQRotation(LL.LL_ROOT.task)
        #     nextGate["Qubit Device"] = qd_Q1  # qubit 1
        #     nextGate["Rotation Axis"] = 'X'  # drive on X
        #     nextGate["Rotation Angle"] = 0.5  # pi pulse
        #     nextGate["Task Dependences"] = [prevGate, gate2]
        #     prevGate=nextGate

        pass

    def run_event_loop(self):
        self.share_state_now = True
        self.quit = False
        while not self.quit:
            sleep(0.01)
            # check the interface creation queue to connect to interfaces on other processes as needed
            try:
                q_val = self.interface_creation_q.get_nowait()
                pipe = multiprocessing.reduction.rebuild_pipe_connection(*q_val[1])
                self.connections.append(LLControlConnection(self,pipe))
            except Empty:
                pass

            # allow all connections to process messages from their interfaces thread
            for conn in self.connections:
                conn.check_pipe()

            if self.share_state_now:
                if len(self.connections)>0:
                    self.share_system_state() # won't call this from the loop, will call this after significant state changes
                    self.share_state_now = False

    def share_system_state(self):
        length = sizeof(c_double)
        length += LL.LL_ROOT.binaryshare_set_location_get_length(length)

        print "Dumping root " + str(length/1024.)+ " kB."

        for conn in self.connections:
            conn.share_system_state(length)


class LLControlConnection(object):
    def __init__(self, controller, interface_pipe):
        self.controller = controller
        self.interface_pipe = interface_pipe
        self.state_share_bufA = None
        self.state_share_bufB = None
        self.state_sharing = False

    def check_pipe(self):
        try:

            while self.interface_pipe.poll():
                p_val = self.interface_pipe.recv()
                if p_val[0]==LLControlInterface.cmd_save_and_quit:
                    element = LL.LL_ROOT.create_xml_element()
                    tree = xmlet.ElementTree(element=element)
                    tree.write(".\\shutdown-state.xml")
                    self.controller.quit = True
                elif p_val[0]==LLControlInterface.cmd_load_shutdown_state:
                    LL.LL_ROOT.remove() #todo: check this destroys old root object? (and all other objects?)
                    tree = xmlet.ElementTree(file=".\\shutdown-state.xml")
                    element = tree.getroot()
                    LLObject.from_xml_element(element) # also sets the new root
                    LL.LL_ROOT.expsetups.ll_children[0].update_coupling_refs()
                    LL.LL_ROOT.task.create_or_update_subtasks_internal()
                    self.controller.share_state_now = True
                elif p_val[0]==LLControlInterface.cmd_load_test_state:
                    LL.LL_ROOT.remove()
                    LL.LL_ROOT = LL.LLRoot.from_blank()
                    self.controller.add_test_system()
                    LL.LL_ROOT.expsetups.ll_children[0].update_coupling_refs()
                    LL.LL_ROOT.task.create_or_update_subtasks_internal()
                    self.controller.share_state_now = True
                elif p_val[0]==LLControlInterface.cmd_state_sharing:
                    self.enable_system_state_share(sharing_enabled=p_val[1], mmap_name=p_val[2], mmap_size=p_val[3], mutex_name=p_val[4])
                elif p_val[0]==LLControlInterface.cmd_state_pipe:
                    self.state_pipe = multiprocessing.reduction.rebuild_pipe_connection(*p_val[1][1])
                elif p_val[0]==LLControlInterface.cmd_set_parameter:
                    target_object = cast(p_val[1],py_object).value
                    target_param = target_object.get_parameter(p_val[2])
                    if p_val[3] is None:
                        val = None
                    else:
                        if target_param.ptype <= LLObjectParameter.PTYPE_STR:
                            val = p_val[3]
                        elif target_param.ptype == LLObjectParameter.PTYPE_NUMPY:
                            val = p_val[3]  # todo: i think this probably doesn't work
                        elif target_param.ptype == LLObjectParameter.PTYPE_LLOBJECT:  # object or param
                            val = cast(p_val[3],py_object).value
                        elif target_param.ptype == LLObjectParameter.PTYPE_LLPARAMETER:  # object or param
                            val = cast(p_val[3][0],py_object).value.get_parameter(p_val[3][1])
                        elif target_param.ptype == LLObjectParameter.PTYPE_LLOBJECT_LIST:  # object or param lists
                            val = [cast(item, py_object).value for item in p_val[3]]
                        elif target_param.ptype == LLObjectParameter.PTYPE_LLPARAMETER_LIST:  # object or param lists
                            val = [cast(item[0], py_object).value.get_parameter(item[1]) for item in p_val[3]]
                        else:
                            val = None
                    target_param.set_value(val)
                    if isinstance(target_object, LLTask):
                        #todo: should  this really be here? updates the coupling list
                        LL.LL_ROOT.expsetups.ll_children[0].update_coupling_refs()
                        target_object.create_or_update_subtasks_internal()
                    self.controller.share_state_now = True
                elif p_val[0]==LLControlInterface.cmd_create_llobject:
                    classname = p_val[1]
                    id = p_val[2]
                    if id is None:
                        parent_obj = None
                    else:
                        parent_obj = cast(id ,py_object).value
                    klass = getattr(LL, classname)
                    klass(parent_obj)
                    self.controller.share_state_now = True
                elif p_val[0]==LLControlInterface.cmd_remove_llobject:
                    obj = cast(p_val[1],py_object).value
                    obj.remove()
                    self.controller.share_state_now = True
                elif p_val[0]==LLControlInterface.cmd_create_lltask:
                    classname=p_val[1]
                    parent_task=cast(p_val[2], py_object).value
                    if p_val[3] is None:
                        after_task = None
                    else:
                        after_task = cast(p_val[3], py_object).value
                    insert_operation = p_val[4]
                    # create the new task inside the parent task given
                    klass = getattr(LL,classname)
                    newtask = klass(parent_task)
                    # set dependence of this task
                    if after_task is not None:
                        newtask["Task Dependences"] += [after_task,]
                        # move other tasks behind this task if we're doing an insert.
                        if insert_operation:
                            for sibling_task in parent_task.ll_children:
                                if sibling_task != newtask:
                                    dependences = sibling_task["Task Dependences"]
                                    for i in range(len(dependences)):
                                        if dependences[i]==after_task:
                                            dependences[i]=newtask
                    self.controller.share_state_now = True
                elif p_val[0]==LLControlInterface.cmd_remove_lltask:
                    task = cast(p_val[1], py_object).value
                    parent_task = task.ll_parent
                    deps = task["Task Dependences"]
                    task.remove()
                    sibling_tasks = parent_task.ll_children
                    for sibling in sibling_tasks:
                        siblingdeps = sibling["Task Dependences"]
                        if task in siblingdeps:
                            siblingdeps.remove(task)
                            if p_val[2]:
                                for d in deps:
                                    if d not in siblingdeps:
                                        siblingdeps.append(d)
                    self.controller.share_state_now = True
                elif p_val[0]==LLControlInterface.cmd_plan_and_execute:
                    LL.LL_ROOT.task.execute()
                    self.controller.share_state_now = True

        except IOError:
            QtWidgets.qApp.quit()

    def enable_system_state_share(self, sharing_enabled, mmap_name, mmap_size, mutex_name):
        self.state_sharing = sharing_enabled
        self.state_mmap_name = mmap_name
        self.state_mmap_size = mmap_size
        self.state_mutex_name =  mutex_name

        self.state_mutex = (NamedMutex(self.state_mutex_name + 'A'), NamedMutex(self.state_mutex_name + 'B'))
        self.state_mmap = (mmap(-1, self.state_mmap_size, self.state_mmap_name + 'A'),
                           mmap(-1, self.state_mmap_size, self.state_mmap_name + 'B'))

    def share_system_state(self, size):
        if not self.state_sharing:
            return

        if size > self.state_mmap_size:
            print "State share size %fMB exceeds %fMB mmap file." % (size/1024./1024., self.state_mmap_size/1024./1024.)

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
        loc = addressof(dump_buf)
        time =  timer()
        c_double.from_address(loc).value = time
        LL.LL_ROOT.binaryshare_dump(loc)

        # release the mutex so the other process can access the data
        self.state_mutex[mutexid].release()
        stop = timer()
        time = stop-start
        #print("Dumped in " + str(time))


# it's only a qobject so we can use some nice slots
class LLControlInterface(Qt.QObject):
    system_state_updated = Qt.pyqtSignal()

    cmd_load_test_state = -2
    cmd_load_shutdown_state = -1
    cmd_save_and_quit = 0
    cmd_state_sharing = 1
    cmd_state_pipe = 2
    cmd_set_parameter = 3
    cmd_create_llobject = 4
    cmd_remove_llobject = 5
    cmd_create_lltask = 6
    cmd_remove_lltask = 7
    cmd_plan_and_execute = 8

    def __init__(self, interface_creation_q):
        super(LLControlInterface,self).__init__()
        self.interface_creation_q = interface_creation_q
        self.control_pipe =  self.connect_to_controller()

        self.state_sharing = False
        self.state_root = None
        self.state_instruments = None
        self.state_devices = None
        self.state_pulses = None
        self.state_task = None
        self.state_exp_setups = None
        self.state_exp_setup = None
        self.state_couplings = None

    def connect_to_controller(self):
        local_pipe, remote_pipe = multiprocessing.Pipe()
        self.control_pipe = local_pipe
        try:
            self.interface_creation_q.put(multiprocessing.reduction.reduce_connection(remote_pipe))
        except Full:
            pass
        return local_pipe

    def enable_system_state_share(self, bufsize=1*2**28): # default 256 MB buffer
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

        # local_pipe, remote_pipe = multiprocessing.Pipe()
        # self.state_pipe = local_pipe
        # self.control_pipe.send((self.cmd_state_pipe, multiprocessing.reduction.reduce_connection(remote_pipe)))

        self.state_prevtime = 0.

    def update_system_state(self):
        # check for a newer state
        if not self.state_sharing:
            return
        something_loaded = False
        if self.state_mutex[0].acquire(0):
            dump_buf = c_void_p.from_buffer(self.state_mmap[0])
            loc = addressof(dump_buf)
            if c_double.from_address(loc).value>self.state_prevtime:
                print("GUI loading state from buffer A")
                self.load_system_state(loc)
                self.state_prevtime = c_double.from_address(loc).value
                something_loaded = True
            self.state_mutex[0].release()
        elif self.state_mutex[1].acquire(0):
            dump_buf = c_void_p.from_buffer(self.state_mmap[1])
            loc = addressof(dump_buf)
            if c_double.from_address(loc).value>self.state_prevtime:
                print("GUI loading state from buffer B")
                self.load_system_state(loc)
                self.state_prevtime = c_double.from_address(loc).value
                something_loaded = True
            self.state_mutex[1].release()
        if something_loaded:
            self.state_instruments = self.state_root["Instruments"].ll_children
            self.state_devices = self.state_root["Devices"].ll_children
            #print("devices:", len(self.state_devices))
            self.state_pulses = self.state_root["Pulses"]
            self.state_task = self.state_root["Task"]
            self.state_exp_setups = self.state_root["Experiment Setups"].ll_children
            self.state_couplings = self.state_root["Couplings"].ll_children
            if len(self.state_exp_setups)>0:
                self.state_exp_setup = self.state_exp_setups[0]
            self.system_state_updated.emit()

    def load_system_state(self, dump_loc):
        dump_abs = dump_loc
        dump_loc += sizeof(c_double) #skip over timer
        if self.state_root is not None:
            self.state_root.destroy_hierarchy()
            self.state_root = None
        self.state_root = LLObjectInterface()
        self.state_root.binaryshare_load(dump_loc)
        self.state_root.binaryshare_loadrefs(dump_loc,dump_abs)
        #self.state_root.print_hierarchy()

    def set_parameter(self, param, value):
        if value is None:
            val = None
        else:
            if param.ptype <= LLObjectParameter.PTYPE_STR:
                val = value
            elif param.ptype == LLObjectParameter.PTYPE_NUMPY:
                val = value #todo: i think this probably doesn't work
            elif param.ptype == LLObjectParameter.PTYPE_LLOBJECT: # object or param
                val = value.ref_id
            elif param.ptype == LLObjectParameter.PTYPE_LLPARAMETER: # object or param
                val = (value.obj_ref.ref_id, value.label)
            elif param.ptype == LLObjectParameter.PTYPE_LLOBJECT_LIST: # object or param lists
                val = [item.ref_id for item in value]
            elif param.ptype == LLObjectParameter.PTYPE_LLPARAMETER_LIST: # object or param lists
                val = [(item.obj_ref.ref_id, item.label) for item in value]
            else:
                val = None

        self.control_pipe.send((self.cmd_set_parameter, param.obj_ref.ref_id, param.label, val))

    def create_llobject(self, classname, parentobj=None):
        if parentobj is None:
            id = None
        else:
            id = parentobj.ref_id
        self.control_pipe.send((self.cmd_create_llobject,classname,id))

    def remove_llobject(self, obj):
        if obj is None:
            return
        self.control_pipe.send((self.cmd_remove_llobject,obj.ref_id))

    def create_lltask(self, classname, parent_task, after_task=None, insert_operation=False):
        if parent_task is None:
            return
        if after_task is None:
            after_id = None
        else:
            after_id = after_task.ref_id
        self.control_pipe.send((self.cmd_create_lltask, classname, parent_task.ref_id, after_id, insert_operation))

    def remove_lltask(self, task, move_dependents=False):
        if task is None:
            return
        self.control_pipe.send((self.cmd_remove_lltask, task.ref_id, move_dependents))

    def plan_and_execute(self):
        self.control_pipe.send((self.cmd_plan_and_execute, ))

    def save_and_quit(self):
        self.control_pipe.send((self.cmd_save_and_quit, ))

    def load_shutdown_state(self):
        self.control_pipe.send((self.cmd_load_shutdown_state, ))

    def load_test_state(self):
        self.control_pipe.send((self.cmd_load_test_state, ))

class LLObjectInterface(object):
    def __init__(self):
        self.ref_id = 0
        self.ll_params = []
        self.ll_children = []
        self.ll_parent = None
        self.classname = ""

    def binaryshare_load(self, loc):
        start = loc
        c_int.from_address(loc).value = id(self) # store own location
        loc += sizeof(c_int)
        bytelength = c_int.from_address(loc).value
        loc += sizeof(c_int)

        classnamelen =  c_int.from_address(loc).value
        loc += sizeof(c_int)
        self.classname = (c_char*classnamelen).from_address(loc).value
        loc += classnamelen

        self.ref_id = c_int.from_address(loc).value
        loc += sizeof(c_int)
        num_children = c_int.from_address(loc).value
        loc += sizeof(c_int)
        num_params = c_int.from_address(loc).value
        loc += sizeof(c_int)

        for i in range(num_children):
            child = self.add_child()
            loc = child.binaryshare_load(loc)

        for i in range(num_params):
            param = self.add_parameter()
            loc = param.binaryshare_load(loc)

        return start + bytelength

    def binaryshare_loadrefs(self, loc, dump):
        start = loc
        loc += sizeof(c_int)
        bytelength = c_int.from_address(loc).value
        loc += sizeof(c_int)
        classnamelen = c_int.from_address(loc).value
        loc += sizeof(c_int) + classnamelen

        loc += 3*sizeof(c_int)

        for child in self.ll_children:
            loc = child.binaryshare_loadrefs(loc,dump)

        for param in self.ll_params:
            loc = param.binaryshare_loadrefs(loc,dump)

        return start + bytelength

    def add_parameter(self):
        param = LLParameterInterface()
        param.obj_ref = self
        self.ll_params.append(param)
        return param

    def add_child(self):
        child = LLObjectInterface()
        child.ll_parent = self
        self.ll_children.append(child)
        return child

    #todo: add a similar function to the real llobject class?
    def destroy_hierarchy(self):
        for param in self.ll_params:
            param.destroy_hierarchy()
        for child in self.ll_children:
            child.destroy_hierarchy()
        del self.ll_children[:]
        self.ll_parent = None

    def print_hierarchy(self,indent=0):
        print "x"
        for param in self.ll_params:
            print (" "*indent)+"p_"+param.label
        for child in self.ll_children:
            child.print_hierarchy(indent+4)

    def get_parameter(self, label):
        for param in self.ll_params:
            if param.label == label:
                return param
        return None

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.get_parameter(item).value
        else:
            return None

    def __setitem__(self, item, val):
        if isinstance(item, str):
            return self.get_parameter(item).value
        else:
            return None

class LLParameterInterface(object):
    def __init__(self):
        self.obj_ref=None
        self.ptype=0
        self.value=None
        self.label=""
        self.unit=""
        self.xvals = None
        self.xlabel = ""
        self.xunit = ""
        self.value_dict = None
        self.select_from = None
        self.read_only = False
        self.visible =  False
        self.ptype_filter = tuple()

    def from_string(self, string):
        if self.ptype==LLObjectParameter.PTYPE_FLOAT or self.ptype==LLObjectParameter.PTYPE_FLOAT:
            string = ''.join(string.split())
            string =  string.replace(",","")
            lowcase_string = string.lower()

            if lowcase_string.endswith(self.unit.lower()):
                string = string[:-len(self.unit)]
            expchar = string[-1]
            expchar_lc = expchar.lower()

            if expchar_lc=='k':
                exp = 1
            elif expchar=='M':
                exp = 2
            elif expchar_lc=='g':
                exp = 3
            elif expchar_lc=='t':
                exp = 4
            elif expchar == 'm':
                exp = -1
            elif expchar_lc == 'u':
                exp = -2
            elif expchar_lc == 'n':
                exp = -3
            elif expchar_lc == 'p':
                exp = -4
            elif expchar_lc == 'f':
                exp = -5
            else:
                exp = 0

            numbers = re.findall("[-+]?\d+[\.]?\d*[eE]?[-+]?\d*", string)
            value = float(numbers[0]) * 1000**(exp)

            return value
        else:

            return string


    def to_string(self):
        def llobj_to_string(obj):
            if obj is None or len(obj.ll_params)==0:
                return 'None'
            else:
                if obj.ll_params[0].ptype == LLObjectParameter.PTYPE_STR:
                    return str(obj.ll_params[0].value)
                else:
                    return "%s{%i}" % (obj.classname, obj.ref_id)

        if self.ptype==LLObjectParameter.PTYPE_INT or self.ptype==LLObjectParameter.PTYPE_FLOAT:
            if self.unit not in ('pi','dBm'):
                try:
                    log1000 = math.log(self.value, 1000.0)
                except:
                    log1000 = 0.0
                if log1000 >= 0.0:
                    if log1000 < 1.0:
                        exp = 0
                        expchar = ''
                    elif log1000 < 2.0:
                        exp = 1
                        expchar = 'k'
                    elif log1000 < 3.0:
                        exp = 2
                        expchar = 'M'
                    elif log1000 < 4.0:
                        exp = 3
                        expchar = 'G'
                    else:
                        exp = 4
                        expchar = 'T'
                else:
                    if log1000 >= -1.0:
                        exp = -1
                        expchar = 'm'
                    elif log1000 >= -2.0:
                        exp = -2
                        expchar = 'u'
                    elif log1000 >= -3.0:
                        exp = -3
                        expchar = 'n'
                    elif log1000 >= -4.0:
                        exp = -4
                        expchar = 'p'
                    else:
                        exp = -5
                        expchar = 'f'
                sigval = self.value*(1000.0**-exp)
            else:
                sigval = self.value
                exp = 0
                expchar= ''
            return "%.4f %s%s" % (sigval, expchar, self.unit)
        elif self.ptype==LLObjectParameter.PTYPE_LLOBJECT:
            return llobj_to_string(self.value)
        elif self.ptype==LLObjectParameter.PTYPE_LLOBJECT_LIST:
            string = ""
            for val in self.value:
                string += llobj_to_string(val)
                string += ", "
            return string
        else:
            return str(self.value)

    def binaryshare_loadrefs(self, loc, dump):

        def load_string(loc):
            strlen =  c_int.from_address(loc).value
            loc+=sizeof(c_int)
            return (c_char*strlen).from_address(loc).value, loc+strlen

        def load_object(loc):
            addr = c_int.from_address(loc).value
            if addr < 0:
                obj = None
            else:
                ref = c_int.from_address(dump + addr).value
                obj = cast(ref, py_object).value
            return obj, loc+sizeof(c_int)

        loc = self.data_start_loc

        if self.ptype==LLObjectParameter.PTYPE_LLOBJECT or self.ptype==LLObjectParameter.PTYPE_LLPARAMETER:
            self.select_from, loc = load_object(loc)
            ptype_filter_str, loc = load_string(loc)
            self.ptype_filter = eval(ptype_filter_str)

            self.value, loc = load_object(loc)

        elif self.ptype==LLObjectParameter.PTYPE_LLOBJECT_LIST or self.ptype==LLObjectParameter.PTYPE_LLPARAMETER_LIST:
            self.select_from, loc = load_object(loc)
            ptype_filter_str, loc = load_string(loc)
            self.ptype_filter = eval(ptype_filter_str)

            num = c_int.from_address(loc).value
            loc +=sizeof(c_int)
            self.value = []
            for i in range(num):
                obj, loc = load_object(loc)
                self.value.append(obj)

        return self.data_end_loc

    def binaryshare_load(self, loc):
        start = loc

        c_int.from_address(loc).value = id(self) # store own location
        loc += sizeof(c_int)

        end = start + c_int.from_address(loc).value
        loc += sizeof(c_int)

        self.ptype = c_int.from_address(loc).value
        loc += sizeof(c_int)

        def load_string(loc):
            strlen =  c_int.from_address(loc).value
            loc+=sizeof(c_int)
            return (c_char*strlen).from_address(loc).value, loc+strlen

        self.label, loc = load_string(loc)
        self.unit, loc = load_string(loc)
        self.value_dict_str, loc = load_string(loc)
        self.value_dict = eval(self.value_dict_str)

        self.read_only = c_bool.from_address(loc).value
        loc+= sizeof(c_bool)
        self.viewable = c_bool.from_address(loc).value
        loc+= sizeof(c_bool)

        self.data_start_loc = loc

        if self.ptype==LLObjectParameter.PTYPE_BOOL:
            self.value=c_bool.from_address(loc).value
        elif self.ptype==LLObjectParameter.PTYPE_INT:
            self.value=c_int.from_address(loc).value
        elif self.ptype==LLObjectParameter.PTYPE_FLOAT:
            self.value=c_double.from_address(loc).value
        elif self.ptype==LLObjectParameter.PTYPE_STR:
            self.value, loc = load_string(loc)
        elif self.ptype==LLObjectParameter.PTYPE_NUMPY:
            def load_numpy(loc):
                ndim = c_int.from_address(loc).value
                loc+=sizeof(c_int)
                shape = []
                for i in range(ndim):
                    shape.append(c_int.from_address(loc).value)
                    loc+=sizeof(c_int)
                dtypestr, loc = load_string(loc)
                nbytes = c_int.from_address(loc).value
                loc += sizeof(c_int)
                nparray = np.frombuffer(np.core.multiarray.int_asbuffer(loc, nbytes),dtype=dtypestr)
                value = np.copy(nparray)
                value.shape = shape

                return value, loc+nbytes
            self.value, loc = load_numpy(loc)
            self.xlabel, loc = load_string(loc)
            if self.xlabel != "":
                self.xunit, loc = load_string(loc)
                self.xvals, loc = load_numpy(loc)
        self.data_end_loc = end
        return end


    def destroy_hierarchy(self):
        self.obj_ref = None
        if(self.ptype==LLObjectParameter.PTYPE_LLOBJECT or self.ptype==LLObjectParameter.PTYPE_LLPARAMETER):
            self.value = None
        elif(self.ptype==LLObjectParameter.PTYPE_LLPARAMETER_LIST or self.ptype==LLObjectParameter.PTYPE_LLOBJECT_LIST):
            del self.value[:]
