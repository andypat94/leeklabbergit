import LeekLabber as LL
from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg

# import pyqtgraph.examples
# pyqtgraph.examples.run()

class LLQtPlotWidget(pg.PlotWidget):
    def __init__(self, name='LLQtPlotWidget'):
        super(LLQtPlotWidget, self).__init__(name=name)

class LLQtParameterPlotWidgetItem(QtWidgets.QTableWidgetItem):
    def __init__(self, param, npindex):
        if npindex>=0:
            super(LLQtParameterPlotWidgetItem, self).__init__("%s [%i]" % (param.label, npindex))
        else:
            super(LLQtParameterPlotWidgetItem, self).__init__(param.label)
        self.param = param
        self.npindex = npindex
        self.setFlags(self.flags() & ~QtCore.Qt.ItemIsEditable)

class LLQtParameterPlotWidget(QtWidgets.QWidget):
    def __init__(self):
        super(LLQtParameterPlotWidget, self).__init__()

        self.main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.main_layout)

        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.main_layout.addWidget(self.splitter)

        self.plot = LLQtPlotWidget()
        self.splitter.addWidget(self.plot)

        self.table = QtWidgets.QTableWidget()
        self.splitter.addWidget(self.table)
        self.table.itemSelectionChanged.connect(self.selection_changed)
        self.table.setColumnCount(1)
        self.table.horizontalHeader().hide()
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)

        self.selection_changed_disabled = False
        self.obj = None
        self.selectedparams = []

        self.hide()

    def selection_changed(self):
        if self.selection_changed_disabled:
            return

        items =  self.table.selectedItems()

        self.plot.clear()

        for item in items:
            param = item.param
            npindex = item.npindex

            plotargs = dict()

            if npindex == -1:
                y = param.value
            else:
                y = param.value[npindex]

            plotargs['y'] = y

            if param.xvals is not None and param.xvals.shape==y.shape:
                plotargs['x'] = param.xvals

            self.plot.plot(**plotargs)

    def set_object(self, obj):
        self.selection_changed_disabled = True

        if self.obj is not None:
            items = self.table.selectedItems()
            self.selectedparams = [(item.param.label, item.npindex) for item in items]

        self.obj = obj

        self.table.clearContents()
        self.table.setRowCount(0)

        if obj is None:
            return

        items = []

        def add_row(*args,**kwargs):
            r =  self.table.rowCount()
            self.table.setRowCount(r + 1)
            item =  LLQtParameterPlotWidgetItem(*args, **kwargs)
            item.row = r
            self.table.setItem(r, 0, item)
            items.append(item)

        for param in obj.ll_params:
            if param.ptype == LL.LLObjectParameter.PTYPE_NUMPY:
                shape = param.value.shape
                if(len(shape)>1):
                    for npindex in range(shape[0]):
                        add_row(param, npindex)
                else:
                    add_row(param)

        for (label, npindex) in self.selectedparams:
            for item in items:
                if label==item.param.label and npindex==item.npindex:
                    self.table.selectRow(item.row)


        self.selection_changed_disabled = False
        self.selection_changed()

        if self.table.rowCount()==0:
            self.hide()
        else:
            self.show()
