import LeekLabber as LL
import PyQt5.QtCore as Qt
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets

class LLQtSelectionDialog(QtWidgets.QDialog):
    def __init__(self, object_n_parameter=True, list_selection=False):
        super(LLQtSelectionDialog,self).__init__()
        self.object_n_parameter = object_n_parameter
        self.list_selection = list_selection

        self.main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.main_layout)

        self.setWindowTitle("Selection Dialog")

        # create the object window
        self.main_layout.addWidget(QtWidgets.QLabel("Object:"))
        self.object_table = QtWidgets.QTableWidget(0, 1)
        self.object_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        if list_selection and object_n_parameter:
            self.object_table.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        else:
            self.object_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.object_table.horizontalHeader().hide()
        self.object_table.verticalHeader().hide()
        self.object_table.horizontalHeader().setStretchLastSection(True)
        self.main_layout.addWidget(self.object_table)

        if object_n_parameter:
            self.param_table = None
        else:
            self.main_layout.addWidget(QtWidgets.QLabel("Parameter:"))
            self.param_table = QtWidgets.QTableWidget(0,1)
            self.param_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
            if list_selection:
                self.param_table.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
            else:
                self.param_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
            self.param_table.horizontalHeader().hide()
            self.param_table.verticalHeader().hide()
            self.param_table.horizontalHeader().setStretchLastSection(True)
            self.object_table.itemSelectionChanged.connect(self.object_changed)
            self.main_layout.addWidget(self.param_table)

        self.button_clear = QtWidgets.QPushButton("Clear Selection")
        self.button_clear.clicked.connect(self.clear_push)
        self.main_layout.addWidget(self.button_clear)

        self.button_ok =QtWidgets.QPushButton("OK")
        self.button_ok.clicked.connect(self.ok_push)
        self.button_cancel =QtWidgets.QPushButton("Cancel")
        self.button_cancel.clicked.connect(self.cancel_push)
        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.addWidget(self.button_ok)
        self.button_layout.addWidget(self.button_cancel)
        self.main_layout.addLayout(self.button_layout)

    def object_changed(self):
        if len(self.object_table.selectedItems())>0:
            item = self.object_table.selectedItems()[0]
            self.selected_object = item.data(Qt.Qt.UserRole)
            params = self.selected_object.ll_params
        else:
            self.selected_object = None
            params = []

        # set parameters visible
        params =  [param for param in params if param.ptype in self.accepted_ptypes]

        self.param_table.setRowCount(len(params))
        self.param_table.clearContents()
        row = 0
        for param in params:
            item = QtWidgets.QTableWidgetItem(param.label)
            item.setFlags(item.flags() & ~Qt.Qt.ItemIsEditable)
            item.setData(Qt.Qt.UserRole, param)
            self.param_table.setItem(row, 0, item)
            row = row + 1
        pass


    def set_objects(self, all_objects, paramname):
        self.all_objects = all_objects
        self.object_table.setRowCount(len(self.all_objects))
        self.object_table.clearContents()
        row = 0
        for obj in self.all_objects:
            item = QtWidgets.QTableWidgetItem(obj[paramname])
            item.setFlags(item.flags() & ~Qt.Qt.ItemIsEditable)
            item.setData(Qt.Qt.UserRole, obj)
            self.object_table.setItem(row, 0, item)
            row = row + 1

    def set_parameter_filter(self, accepted_ptypes):
        self.accepted_ptypes = accepted_ptypes

    def set_selected_object(self, selected_object):
        self.set_selected_objects([selected_object,])

    def set_selected_parameter(self, selected_parameter):
        if selected_parameter is not None:
            self.set_selected_object(selected_parameter.obj_ref)
            self.set_selected_somethings_in_sometable([selected_parameter,], self.param_table)

    def set_selected_objects(self, selected_objects):
        self.set_selected_somethings_in_sometable(selected_objects, self.object_table)

    def set_selected_somethings_in_sometable(self, somethings, table):
        scrollTo = None
        for row in range(table.rowCount()):
            item = table.item(row, 0)
            obj = item.data(Qt.Qt.UserRole)
            if obj in somethings:
                item.setSelected(True)
                scrollTo = item
            else:
                item.setSelected(False)
        if scrollTo is not None:
            table.scrollToItem(scrollTo, QtWidgets.QTableWidget.EnsureVisible)

    def cancel_push(self):
        self.selected_items = []
        self.selected_item = None
        self.reject()

    def ok_push(self):
        if self.list_selection:
            self.selected_item = None
            self.selected_items = [item.data(Qt.Qt.UserRole) for item in self.object_table.selectedItems()]
        else:
            self.selected_items = []
            if self.object_n_parameter:
                table = self.object_table
            else:
                table = self.param_table
            if len(table.selectedItems())>0:
                self.selected_item = table.selectedItems()[0].data(Qt.Qt.UserRole)
            else:
                self.selected_item = None
        self.accept()

    def clear_push(self):
        if self.object_n_parameter:
            self.object_table.clearSelection()
        else:
            self.param_table.clearSelection()