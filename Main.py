from PyQt5 import QtWidgets
from LeekLabber import *
import LeekLabber.LLDevices as LLDevices
import LeekLabber.LLInstruments as LLInstruments
import LeekLabber.LLTasks as LLTasks
import xml.etree.ElementTree as xmlet

import matplotlib.pyplot as plt

if __name__ == "__main__":

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
    mwcl["Number of Drives"] = 2 # Two drives (one for qubit, one for resonator)
    mwcl["Number of Readouts"] = 1 # One readout (of resonator)
    p_1gs_dac_data =  i_FPGABOX.get_parameter("1GS DAC Data")
    p_2gs_dac_data =  i_FPGABOX.get_parameter("2GS DAC Data")
    p_adc_data =  i_FPGABOX.get_parameter("ADC Data")
    # First drive (for resonator) from 1gs first board
    mwcl["Drive Generators"][0] = i_SGS_RF
    mwcl["DACs for Drives"][0] = p_1gs_dac_data
    mwcl["DAC Channel I"][0] = 0
    mwcl["DAC Channel Q"][0] = 1
    # Second drive (for qubit) from 2gs first board
    mwcl["Drive Generators"][1] = i_SGS_QUBIT
    mwcl["DACs for Drives"][1] = p_2gs_dac_data
    mwcl["DAC Channel I"][1] = 0
    mwcl["DAC Channel Q"][1] = 1
    # First readout (for resonator) from first board
    mwcl["Readout Generators"][0] = i_SGS_LO
    mwcl["ADCs for Readouts"][0] = p_adc_data
    mwcl["ADC Channel I"][0] = 0
    mwcl["ADC Channel Q"][0] = 1
    # This line is for measuring the resonator and controlling the qubit
    mwcl["Transmission (Not Reflection)"] = True
    mwcl["Connected Devices"] += [qd_Q1, qd_R1]

    # Prepare an experiment with a single qubit rotation
    gate = LLTasks.LLTaskSingleQRotation(LL.LL_ROOT.task)
    gate["Qubit Device"] = qd_Q1 #qubit 1
    gate["Rotation Axis"] = 'X' # drive on X
    gate["Rotation Angle"] = 0.5 # pi pulse

    gate2 = LLTasks.LLTaskDelay(LL.LL_ROOT.task)
    gate2["Delay Time"] = 1e-6
    gate2["Task Dependences"] = [gate,]

    gate3 = LLTasks.LLTaskSingleQRotation(LL.LL_ROOT.task)
    gate3["Qubit Device"] = qd_Q1 #qubit 1
    gate3["Rotation Axis"] = 'X' # drive on X
    gate3["Rotation Angle"] = 0.5 # pi pulse
    gate3["Task Dependences"] = [gate2,]

    #large number of gates test
    prevGate = gate3
    for i in range(100):
        nextGate = LLTasks.LLTaskDelay(LL.LL_ROOT.task)
        nextGate["Delay Time"] = np.random.rand(1)[0]*1000.0e-9
        nextGate["Task Dependences"] = [gate3,]
        prevGate=nextGate

        nextGate = LLTasks.LLTaskSingleQRotation(LL.LL_ROOT.task)
        nextGate["Qubit Device"] = qd_Q1  # qubit 1
        nextGate["Rotation Axis"] = 'X'  # drive on X
        nextGate["Rotation Angle"] = 0.5  # pi pulse
        nextGate["Task Dependences"] = [prevGate, ]
        prevGate=nextGate


    LL.LL_ROOT.task.create_or_update_subtasks_internal()

    LL.LL_ROOT.task.execute() # do it!

    # element = LL.LL_ROOT.create_xml_element()
    # newroot = LLObject.from_xml_element(element)
    # LL.LL_ROOT = newroot
    # LL.LL_ROOT.task.create_or_update_subtasks_internal()
    # LL.LL_ROOT.task.execute()

    # app = QtWidgets.QApplication([])
    # app.setQuitOnLastWindowClosed(False)
    # app.exec_()

    plt.plot(i_FPGABOX.get_parameter("2GS DAC Data").get_xvals(),i_FPGABOX["2GS DAC Data"][0])
    plt.plot(i_FPGABOX.get_parameter("2GS DAC Data").get_xvals(),i_FPGABOX["2GS DAC Data"][1])
    #plt.plot(i_FPGABOX.get_parameter("1GS DAC Data").get_xvals(),i_FPGABOX["1GS DAC Data"][0])
    #plt.plot(i_FPGABOX.get_parameter("1GS DAC Data").get_xvals(),i_FPGABOX["1GS DAC Data"][1])
    plt.ylabel('some numbers')
    plt.show()

