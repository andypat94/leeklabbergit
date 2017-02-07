from PyQt5 import QtWidgets
from LeekLabber import *
import LeekLabber.LLDevices as LLDevices
import LeekLabber.LLInstruments as LLInstruments

if __name__ == "__main__":
    testDevice = LLDevices.LLDeviceSimpleQubit()
    testRF = LLInstruments.LLInstrumentRSSGS()
    testFPGA = LLInstruments.LLInstrument4DSPBox()

    app = QtWidgets.QApplication([])
    app.setQuitOnLastWindowClosed(False)
    app.exec_()

