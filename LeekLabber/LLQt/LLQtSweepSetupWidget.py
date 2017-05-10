import LeekLabber as LL
import PyQt5.QtCore as Qt
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets


class LLQtSweepSetupWidget(QtWidgets.QWidget):

    def __init__(self, llci):
        super(LLQtSweepSetupWidget,self).__init__()

        self.setWindowTitle("Sweep Setup")

        self.llci = llci