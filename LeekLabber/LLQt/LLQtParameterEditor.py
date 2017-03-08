import LeekLabber as LL
import PyQt5.QtCore as Qt
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets

class LLQtParameterTable(QtWidgets.QWidget):

    def __init__(self, llci, label=""):
        super(LLQtParameterTable, self).__init__()

        self.llci = llci

        self.setMinimumSize(200, 0)

        self.main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.main_layout)

        if label != "":
            self.main_layout.addWidget(QtWidgets.QLabel(label))

        self.parameter_table = QtWidgets.QTableWidget()
        self.main_layout.addWidget(self.parameter_table)
        self.parameter_table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        hh = self.parameter_table.horizontalHeader()
        #hh.hide()
        #hh.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        #hh.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.parameter_table.verticalHeader().hide()
        self.parameter_table.itemChanged.connect(self.item_changed)
        self.parameter_table.itemDoubleClicked.connect(self.item_double_clicked)
        self.disable_changed = True

    def item_changed(self, item):
        if not self.disable_changed:
            param = item.data(Qt.Qt.UserRole)
            if param.ptype == LL.LLObjectParameter.PTYPE_FLOAT or param.ptype == LL.LLObjectParameter.PTYPE_INT:
                self.llci.set_parameter(param, param.from_string(item.text()))
            elif param.ptype == LL.LLObjectParameter.PTYPE_STR:
                self.llci.set_parameter(param, item.text())

    def combo_index_changed(self, val):
        combo = self.sender()
        param = combo.ll_param
        value = combo.itemData(combo.currentIndex())
        self.llci.set_parameter(param, value)

    def item_double_clicked(self, item):
        param = item.data(Qt.Qt.UserRole)
        if param is None:
            return
        if not param.read_only:
            LL.LLQtSelectionDialog.autodialog_param(self.llci, param)

    def set_objects(self, ll_objs):

        self.disable_changed = True

        # params to show
        self.parameter_table.clearContents()
        if len(ll_objs) == 0:
            return

        ll_obj =  ll_objs[0]

        params = [param.label for param in ll_obj.ll_params if param.viewable]
        self.parameter_table.setColumnCount(len(params))
        self.parameter_table.setRowCount(len(ll_objs))

        hh = self.parameter_table.horizontalHeader()
        self.parameter_table.setHorizontalHeaderLabels(params)

        for c in range(len(params)):
            if c==len(params)-2:
                hh.setSectionResizeMode(c, QtWidgets.QHeaderView.Stretch)
            else:
                hh.setSectionResizeMode(c, QtWidgets.QHeaderView.ResizeToContents)

        o = 0
        for ll_obj in ll_objs:
            p = 0
            for paramlabel in params:
                param = ll_obj.get_parameter(paramlabel)
                if param is not None:
                    if param.value_dict is None:
                        if param.ptype == LL.LLObjectParameter.PTYPE_BOOL:
                            combo = QtWidgets.QComboBox()
                            combo.addItem('True', True)
                            combo.addItem('False', False)
                            index = combo.findData(param.value)
                            combo.setCurrentIndex(index)
                            self.parameter_table.setCellWidget(o, p, combo)
                            combo.ll_param = param
                            combo.currentIndexChanged.connect(self.combo_index_changed)
                            combo.setEnabled(not param.read_only)
                        else:
                            item = QtWidgets.QTableWidgetItem(param.to_string())
                            item.setData(Qt.Qt.UserRole, param)
                            self.parameter_table.setItem(o, p, item)
                            editable_type = param.ptype in (
                            LL.LLObjectParameter.PTYPE_INT, LL.LLObjectParameter.PTYPE_FLOAT,
                            LL.LLObjectParameter.PTYPE_STR)
                            editable = (not param.read_only) and editable_type
                            if editable:
                                item.setFlags(item.flags() | Qt.Qt.ItemIsEditable)
                            else:
                                item.setFlags(item.flags() & ~Qt.Qt.ItemIsEditable)
                    else:
                        combo = QtWidgets.QComboBox()
                        for key, value in param.value_dict.items():
                            combo.addItem(key, value)
                        index = combo.findData(param.value)
                        combo.setCurrentIndex(index)
                        self.parameter_table.setCellWidget(o, p, combo)
                        combo.ll_param = param
                        combo.currentIndexChanged.connect(self.combo_index_changed)
                        combo.setEnabled(not param.read_only)
                p += 1
            o += 1

        self.disable_changed = False

class LLQtParameterEditor(QtWidgets.QWidget):

    def __init__(self, llci):
        super(LLQtParameterEditor,self).__init__()

        self.llci = llci

        self.setMinimumSize(200,0)

        self.main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.main_layout)


        self.object_name_label = QtWidgets.QLabel("LLObject Name")
        self.main_layout.addWidget(self.object_name_label)

        self.parameter_table = QtWidgets.QTableWidget()
        self.main_layout.addWidget(self.parameter_table)
        self.parameter_table.setColumnCount(2)
        self.parameter_table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        hh = self.parameter_table.horizontalHeader()
        hh.hide()
        hh.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.parameter_table.verticalHeader().hide()
        self.parameter_table.itemChanged.connect(self.item_changed)
        self.parameter_table.itemDoubleClicked.connect(self.item_double_clicked)
        self.disable_changed = True

    def item_changed(self, item):
        if not self.disable_changed:
            param = item.data(Qt.Qt.UserRole)
            if param.ptype == LL.LLObjectParameter.PTYPE_FLOAT or param.ptype == LL.LLObjectParameter.PTYPE_INT:
                self.llci.set_parameter(param, param.from_string(item.text()))
            elif param.ptype == LL.LLObjectParameter.PTYPE_STR:
                self.llci.set_parameter(param, item.text())

    def combo_index_changed(self, val):
        combo = self.sender()
        param = combo.ll_param
        value = combo.itemData(combo.currentIndex())
        self.llci.set_parameter(param, value)

    def item_double_clicked(self, item):
        param = item.data(Qt.Qt.UserRole)
        if param is None:
            return
        if not param.read_only:
            LL.LLQtSelectionDialog.autodialog_param(self.llci, param)

    def set_object(self, ll_obj):

        self.disable_changed =  True


        #params to show
        self.parameter_table.clearContents()
        if ll_obj is None:
            self.object_name_label.setText("None")
            return

        self.object_name_label.setText("%s{%i}"%(ll_obj.classname,ll_obj.ref_id))
        params = [param for param in ll_obj.ll_params if param.viewable]
        self.parameter_table.setRowCount(len(params))

        p=0
        for param in params:
            item = QtWidgets.QTableWidgetItem(param.label)
            item.setFlags(item.flags() & ~Qt.Qt.ItemIsEditable)
            self.parameter_table.setItem(p,0, item)
            if param.value_dict is None:
                if param.ptype == LL.LLObjectParameter.PTYPE_BOOL:
                    combo = QtWidgets.QComboBox()
                    combo.addItem('True',True)
                    combo.addItem('False',False)
                    index = combo.findData(param.value)
                    combo.setCurrentIndex(index)
                    self.parameter_table.setCellWidget(p, 1, combo)
                    combo.ll_param = param
                    combo.currentIndexChanged.connect(self.combo_index_changed)
                    combo.setEnabled(not param.read_only)
                else:
                    item = QtWidgets.QTableWidgetItem(param.to_string())
                    item.setData(Qt.Qt.UserRole, param)
                    self.parameter_table.setItem(p,1,item)
                    editable_type = param.ptype in (LL.LLObjectParameter.PTYPE_INT, LL.LLObjectParameter.PTYPE_FLOAT, LL.LLObjectParameter.PTYPE_STR)
                    editable = (not param.read_only) and editable_type
                    if editable:
                        item.setFlags(item.flags() | Qt.Qt.ItemIsEditable)
                    else:
                        item.setFlags(item.flags() & ~Qt.Qt.ItemIsEditable)
            else:
                combo = QtWidgets.QComboBox()
                for key,value in param.value_dict.items():
                    combo.addItem(key, value)
                index = combo.findData(param.value)
                combo.setCurrentIndex(index)
                self.parameter_table.setCellWidget(p,1,combo)
                #todo: write below
                combo.ll_param = param
                combo.currentIndexChanged.connect(self.combo_index_changed)
                combo.setEnabled(not param.read_only)
            p += 1

        self.disable_changed = False