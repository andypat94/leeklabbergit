import LeekLabber as LL
import PyQt5.QtCore as Qt
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets
import os

class LLQtSystemTray(QtWidgets.QSystemTrayIcon):
    def __init__(self, llci):
        super(LLQtSystemTray,self).__init__()

        dirname = os.path.dirname(os.path.realpath(__file__))
        self.phi_icon =QtGui.QIcon(dirname+"\\physics-48.png")
        self.setIcon(self.phi_icon)

        self.llci = llci


        llci.enable_system_state_share()

        self.state_timer = Qt.QTimer()
        self.state_timer.timeout.connect(llci.update_system_state)
        self.state_timer.start(100)

        llci.load_shutdown_state()

        self.setVisible(True)

        self.menu = QtWidgets.QMenu()
        self.setContextMenu(self.menu)
        self.actLoad = self.menu.addAction("Load")
        self.actLoad.triggered.connect(self.menuLoad)
        self.actInstruments = self.menu.addAction("Instruments")
        self.actInstruments.triggered.connect(self.menuInstruments)
        self.actDevices = self.menu.addAction("Devices")
        self.actDevices.triggered.connect(self.menuDevices)
        self.actExpSetup = self.menu.addAction("Experiment Setup")
        self.actExpSetup.triggered.connect(self.menuExpSetup)
        self.actTaskSetup = self.menu.addAction("Task Setup")
        self.actTaskSetup.triggered.connect(self.menuTaskSetup)
        self.actQuit = self.menu.addAction("Quit")
        self.actQuit.triggered.connect(self.menuQuit)
        self.setContextMenu(self.menu)

        self.expSetupWidget = LL.LLQtExpSetupWidget(llci)
        self.expSetupWidget.setWindowIcon(self.phi_icon)
        self.expSetupWidget.show()

        self.taskSetupWidget = LL.LLQtTaskSetupWidget(llci)
        self.taskSetupWidget.setWindowIcon(self.phi_icon)
        self.taskSetupWidget.show()

        self.instrumentsWidget = LL.LLQtInstrumentsWidget(llci)
        self.instrumentsWidget.setWindowIcon(self.phi_icon)
        self.instrumentsWidget.show()

        self.devicesWidget = LL.LLQtDevicesWidget(llci)
        self.devicesWidget.setWindowIcon(self.phi_icon)
        self.devicesWidget.show()

    def show_window(self, widget):
        widget.show()
        if (widget.windowState() == Qt.Qt.WindowMinimized):
            widget.setWindowState(Qt.Qt.WindowNoState)
        widget.activateWindow()
        widget.raise_()

    def menuExpSetup(self):
        self.show_window(self.expSetupWidget)

    def menuTaskSetup(self):
        self.show_window(self.taskSetupWidget)

    def menuInstruments(self):
        self.show_window(self.instrumentsWidget)

    def menuDevices(self):
        self.show_window(self.devicesWidget)

    def menuQuit(self):
        self.llci.save_and_quit()
        QtWidgets.QApplication.quit()

    def menuLoad(self):
        self.llci.load_shutdown_state()
