from PyQt5 import QtWidgets
from LeekLabber import *
import LeekLabber.LLDevices as LLDevices
import LeekLabber.LLInstruments as LLInstruments

if __name__ == "__main__":

    # Create Quantum Devices
    qd_Q1 = LLDevices.LLDeviceSimpleQubit()
    qd_R1 = LLDevices.LLDeviceSimpleResonator()

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

    # Create an Experimental Setup
    exp_setup = LLExpSetup()

    # Create one control line for the setup
    mwcl = LLMicrowaveControlLine(NDrives=2,NReadouts=1)
    # Set up first control line (to qubit 1, resonator 1)
    p_1gs_dac_data =  i_FPGABOX.get_parameter("1GS DAC Data")
    p_2gs_dac_data =  i_FPGABOX.get_parameter("2GS DAC Data")
    p_adc_data =  i_FPGABOX.get_parameter("ADC Data")
    # First drive (for resonator) from 1gs first board
    mwcl["DACs for Drives"][0] = p_1gs_dac_data
    mwcl["DAC Channel I"][0] = 0
    mwcl["DAC Channel Q"][0] = 1
    # Second drive (for qubit) from 2gs first board
    mwcl["DACs for Drives"][1] = p_2gs_dac_data
    mwcl["DAC Channel I"][1] = 0
    mwcl["DAC Channel Q"][1] = 1
    # First readout (for resonator) from first board
    mwcl["ADCs for Readouts"][0] = p_adc_data
    mwcl["ADC Channel I"][0] = 0
    mwcl["ADC Channel Q"][0] = 1
    # This line is for measuring the resonator and controlling the qubit
    mwcl["Transmission (Not Reflection)"] = True
    mwcl["Connected Devices"] += [qd_Q1, qd_R1]
    # Add the control line to the setup
    exp_setup.addControlLine(mwcl)

    app = QtWidgets.QApplication([])
    app.setQuitOnLastWindowClosed(False)
    app.exec_()

