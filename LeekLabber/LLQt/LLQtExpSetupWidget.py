import LeekLabber as LL
import PyQt5.QtCore as Qt
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets

class LLQtExpSetupWidget(QtWidgets.QWidget):
    def __init__(self, llci):
        super(LLQtExpSetupWidget,self).__init__()

        self.setWindowTitle("Experimental Setup")
        self.llci = llci
        self.llci.system_state_updated.connect(self.llci_update)

        #self.update()

    def llci_update(self):
        # if self.llci.state_root is None or self.llci.state_root["Experiment Setups"] is None or len(self.llci.state_root.expsetups.ll_children)==0:
        #     return
        # exp_setup =  self.llci.state_root.expsetups.ll_children[0]
        # print ("Lines = " + str(len(exp_setup["Microwave Control Lines"])))
        if self.llci.state_root is None:
            return

        print("update")