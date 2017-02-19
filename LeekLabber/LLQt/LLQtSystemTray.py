import LeekLabber as LL
import PyQt5.QtCore as Qt
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets

class LLQtSystemTray(QtWidgets.QSystemTrayIcon):
    def __init__(self, llci):
        super(LLQtSystemTray,self).__init__()

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
        self.actQuit = self.menu.addAction("Quit")
        self.actQuit.triggered.connect(self.menuQuit)
        self.setContextMenu(self.menu)

        self.expSetupWidget = LL.LLQtExpSetupWidget(llci)

        self.expSetupWidget.show()

    def menuExpSetup(self):
        self.expSetupWidget.show()

    def menuQuit(self):
        QtWidgets.QApplication.quit()
