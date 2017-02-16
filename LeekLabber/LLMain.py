import LeekLabber as LL
import PyQt5.QtCore as Qt
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets
from time import sleep

LL.CONTROLLER = None

def start_leeklabber():
    Qt.pyqtRemoveInputHook() # we're handling threading ourselves
    app = QtWidgets.QApplication([]) # create a Qt application

    # start the LeekLabber controller on a new thread
    if LL.CONTROLLER is None:
        LL.CONTROLLER = LL.LLController()
    thread = Qt.QThread()
    LL.CONTROLLER.moveToThread(thread)
    thread.start()

    # create an interface to the leeklabber controller
    llci = LLControlInterface(LL.CONTROLLER)
    # pass nothing but this interface to the gui thread
    tray = LL.LLQtSystemTray(llci)
    app.setQuitOnLastWindowClosed(False)
    app.exec_() #start the gui on this thread (necessary)


class LLController(Qt.QObject):
    def __init__(self):
        super(Qt.QObject, self).__init__()
        self.thread = None

        LL.LL_ROOT = LL.LLRoot.from_blank()  # create a blank global root instance.

class LLControlInterface:
    def __init__(self, control):
        self.control = control

