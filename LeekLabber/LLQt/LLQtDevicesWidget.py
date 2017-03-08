import LeekLabber as LL
import PyQt5.QtCore as Qt
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets


class LLQtDevicesWidget(QtWidgets.QWidget):
    def __init__(self,llci):
        super(LLQtDevicesWidget,self).__init__()
        self.setWindowTitle("Devices")
        self.llci = llci


        self.main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.main_layout)

        self.vsplitter = QtWidgets.QSplitter(Qt.Qt.Vertical)
        self.main_layout.addWidget(self.vsplitter)

        self.splitter = QtWidgets.QSplitter(Qt.Qt.Horizontal)
        self.vsplitter.addWidget(self.splitter)

        self.device_list = LLQtDeviceListWidget(llci)
        self.splitter.addWidget(self.device_list)

        self.param_edit = LL.LLQtParameterEditor(llci)
        self.splitter.addWidget(self.param_edit)

        self.coupling_table = LL.LLQtParameterTable(llci, "Coupling Table")
        self.vsplitter.addWidget(self.coupling_table)

        self.device_list.device_selected.connect(self.param_edit.set_object)
        self.llci.system_state_updated.connect(self.llci_update)

    def llci_update(self):
        self.coupling_table.set_objects(self.llci.state_couplings)


class LLQtDeviceListWidget(QtWidgets.QWidget):
    device_selected = Qt.pyqtSignal([object])

    def __init__(self, llci):
        super(LLQtDeviceListWidget,self).__init__()
        self.llci = llci
        self.selected_device = None

        self.main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.main_layout)

        self.device_table = QtWidgets.QTableWidget()
        self.device_table.setColumnCount(2)
        self.device_table.setRowCount(0)
        self.device_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.device_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.device_table.verticalHeader().hide()
        hh = self.device_table.horizontalHeader()
        #hh.hide()
        hh.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.device_table.setHorizontalHeaderLabels(["Name","Class"])
        self.main_layout.addWidget(self.device_table)

        self.device_table.itemSelectionChanged.connect(self.table_selection)
        self.llci.system_state_updated.connect(self.llci_update)

    def table_selection(self):
        if len(self.device_table.selectedItems()) > 0:
            self.selected_device = self.device_table.selectedItems()[0].data(Qt.Qt.UserRole)
        else:
            self.selected_device = None
        self.device_selected.emit(self.selected_device)

    def llci_update(self):
        if self.selected_device is None:
            select_id = -1
        else:
            select_id = self.selected_device.ref_id

        self.device_table.clearContents()
        self.device_table.setRowCount(len(self.llci.state_devices))
        select_row = -1
        r = 0
        for dev in self.llci.state_devices:

            item = QtWidgets.QTableWidgetItem(dev["Device Name"])
            item.setFlags(item.flags() & ~Qt.Qt.ItemIsEditable)
            item.setData(Qt.Qt.UserRole, dev)
            self.device_table.setItem(r, 0, item)
            item = QtWidgets.QTableWidgetItem(dev.classname)
            item.setFlags(item.flags() & ~Qt.Qt.ItemIsEditable)
            self.device_table.setItem(r, 1, item)

            if dev.ref_id == select_id:
                select_row = r
            r+=1

        if select_row >= 0:
            self.device_table.selectRow(select_row)