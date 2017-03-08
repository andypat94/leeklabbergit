import LeekLabber as LL
import PyQt5.QtCore as Qt
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets



class LLQtInstrumentsWidget(QtWidgets.QWidget):
    def __init__(self, llci):
        super(LLQtInstrumentsWidget,self).__init__()
        self.setWindowTitle("Instruments")
        self.llci = llci

        self.main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.main_layout)

        self.splitter = QtWidgets.QSplitter(Qt.Qt.Horizontal)
        self.main_layout.addWidget(self.splitter)

        self.instrument_list = LLQtInstrumentListWidget(llci)
        self.splitter.addWidget(self.instrument_list)

        self.param_edit = LL.LLQtParameterEditor(llci)
        self.splitter.addWidget(self.param_edit)

        self.param_plot = LL.LLQtParameterPlotWidget()
        self.splitter.addWidget(self.param_plot)

        self.instrument_list.instrument_selected.connect(self.param_edit.set_object)
        self.instrument_list.instrument_selected.connect(self.param_plot.set_object)

class LLQtInstrumentListWidget(QtWidgets.QWidget):
    instrument_selected = Qt.pyqtSignal([object])

    def __init__(self, llci):
        super(LLQtInstrumentListWidget,self).__init__()
        self.llci = llci
        self.selected_instrument = None

        self.main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.main_layout)

        self.instrument_table = QtWidgets.QTableWidget()
        self.instrument_table.setColumnCount(3)
        self.instrument_table.setRowCount(0)
        self.instrument_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.instrument_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.instrument_table.verticalHeader().hide()
        hh = self.instrument_table.horizontalHeader()
        #hh.hide()
        hh.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self.instrument_table.setHorizontalHeaderLabels(["Name","Address","Class"])
        self.main_layout.addWidget(self.instrument_table)

        self.instrument_table.itemSelectionChanged.connect(self.table_selection)
        self.llci.system_state_updated.connect(self.llci_update)

    def table_selection(self):
        if len(self.instrument_table.selectedItems()) > 0:
            self.selected_instrument = self.instrument_table.selectedItems()[0].data(Qt.Qt.UserRole)
        else:
            self.selected_instrument = None
        self.instrument_selected.emit(self.selected_instrument)

    def llci_update(self):
        if self.selected_instrument is None:
            select_id = -1
        else:
            select_id = self.selected_instrument.ref_id

        self.instrument_table.clearContents()
        self.instrument_table.setRowCount(len(self.llci.state_instruments))
        select_row = -1
        r = 0
        for inst in self.llci.state_instruments:

            item = QtWidgets.QTableWidgetItem(inst["Instrument Name"])
            item.setFlags(item.flags() & ~Qt.Qt.ItemIsEditable)
            item.setData(Qt.Qt.UserRole, inst)
            self.instrument_table.setItem(r, 0, item)
            item = QtWidgets.QTableWidgetItem(inst["Instrument Address"])
            item.setFlags(item.flags() & ~Qt.Qt.ItemIsEditable)
            self.instrument_table.setItem(r, 1, item)
            item = QtWidgets.QTableWidgetItem(inst.classname)
            item.setFlags(item.flags() & ~Qt.Qt.ItemIsEditable)
            self.instrument_table.setItem(r, 2, item)

            if inst.ref_id == select_id:
                select_row = r
            r+=1

        if select_row >= 0:
            self.instrument_table.selectRow(select_row)