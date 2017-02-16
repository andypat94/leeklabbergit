import LeekLabber as LL
import PyQt5.QtCore as Qt
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets

class LLQtExpSetupWidget(QtWidgets.QWidget):
    def __init__(self, llci):
        super(LLQtExpSetupWidget,self).__init__()

        self.setWindowTitle("Experimental Setup")

        self.llci = llci