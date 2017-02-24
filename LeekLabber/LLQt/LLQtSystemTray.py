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

        self.setVisible(True)

        self.menu = QtWidgets.QMenu()
        self.setContextMenu(self.menu)
        self.actExpSetup = self.menu.addAction("Experiment Setup")
        self.actExpSetup.triggered.connect(self.menuExpSetup)
        self.actTaskSetup = self.menu.addAction("Task Setup")
        self.actTaskSetup.triggered.connect(self.menuTaskSetup)
        self.actQuit = self.menu.addAction("Quit")
        self.actQuit.triggered.connect(self.menuQuit)
        self.setContextMenu(self.menu)

        self.expSetupWidget = LL.LLQtExpSetupWidget(llci)
        self.expSetupWidget.setWindowIcon(self.phi_icon)
        #self.expSetupWidget.show()

        self.taskSetupWidget = LL.LLQtTaskSetupWidget(llci)
        self.taskSetupWidget.setWindowIcon(self.phi_icon)
        self.taskSetupWidget.show()

    def menuExpSetup(self):
        self.expSetupWidget.show()
        if(self.expSetupWidget.windowState()==Qt.Qt.WindowMinimized):
            self.expSetupWidget.setWindowState(Qt.Qt.WindowNoState)
        self.expSetupWidget.activateWindow()
        self.expSetupWidget.raise_()

    def menuTaskSetup(self):
        self.taskSetupWidget.show()
        if(self.taskSetupWidget.windowState()==Qt.Qt.WindowMinimized):
            self.taskSetupWidget.setWindowState(Qt.Qt.WindowNoState)
        self.taskSetupWidget.activateWindow()
        self.taskSetupWidget.raise_()

    def menuQuit(self):
        QtWidgets.QApplication.quit()
