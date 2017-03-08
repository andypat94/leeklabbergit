import LeekLabber as LL
import PyQt5.QtCore as Qt
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets


class LLQtTaskSetupWidget(QtWidgets.QWidget):

    def __init__(self, llci):
        super(LLQtTaskSetupWidget,self).__init__()

        self.setWindowTitle("Task Setup")

        self.llci = llci

        size = QtWidgets.QDesktopWidget().availableGeometry(self).size()

        self.resize(Qt.QSize(size.width()*0.8, size.height()*0.25))
        self.setWindowTitle("Task Setup")

        #main window central widget
        self.main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.main_layout)

        self.splitter = QtWidgets.QSplitter(Qt.Qt.Horizontal)
        self.main_layout.addWidget(self.splitter)

        self.task_container = LLQtTaskContainerWidget(llci, True)
        self.splitter.addWidget(self.task_container)

        self.param_editor = LL.LLQtParameterEditor(llci)
        self.splitter.addWidget(self.param_editor)

        self.splitter.setStretchFactor(0,1)
        self.splitter.setStretchFactor(1,0)

        self.but_execute = QtWidgets.QPushButton("Plan and Execute")
        self.but_execute.clicked.connect(self.execute_clicked)
        self.main_layout.addWidget(self.but_execute)

        self.task_container.task_selection_changed.connect(self.param_editor.set_object)

        self.llci.system_state_updated.connect(self.llci_update)

    def llci_update(self):
        self.task_container.update(self.llci.state_task)

    def execute_clicked(self):
        self.llci.plan_and_execute()

class LLQtTaskContainerWidget(QtWidgets.QWidget):
    task_selection_changed = Qt.pyqtSignal([object])

    def __init__(self, llci, scroller=False):
        super(LLQtTaskContainerWidget, self).__init__()
        self.llci = llci

        self.qtasks = []
        self.task = None
        self.selected_qtask = None
        self.rightclicked_qtask = None

        self.bands = []

        self.scroller = scroller

        self.create_layout()

        self.create_task_inside_menu = QtWidgets.QMenu()
        self.create_task_after_menu = QtWidgets.QMenu()
        self.insert_task_after_menu = QtWidgets.QMenu()
        self.create_task_inside_menu.setTitle("Create Inside..")
        self.create_task_after_menu.setTitle("Create After..")
        self.insert_task_after_menu.setTitle("Insert After..")
        self.menu_list = []

        m=0
        for modulename in LL.LLTasks.LLTASK_MODULENAMES:
            menu_a = QtWidgets.QMenu()
            menu_b = QtWidgets.QMenu()
            menu_c = QtWidgets.QMenu()
            self.create_task_inside_menu.addMenu(menu_a)
            self.create_task_after_menu.addMenu(menu_b)
            self.insert_task_after_menu.addMenu(menu_c)
            menu_a.setTitle(modulename)
            menu_b.setTitle(modulename)
            menu_c.setTitle(modulename)
            self.menu_list += [menu_a, menu_b, menu_c]
            for classname in LL.LLTasks.LLTASK_CLASSNAMES[m]:
                actA = menu_a.addAction(classname)
                actA.triggered.connect((lambda cname=classname: lambda: self.create_task_inside(cname))())
                actB = menu_b.addAction(classname)
                actB.triggered.connect((lambda cname=classname: lambda: self.create_task_after(cname))())
                actC = menu_c.addAction(classname)
                actC.triggered.connect((lambda cname=classname: lambda: self.insert_task_after(cname))())
            m += 1

        #self.setStyleSheet(nice_groupbox_style)

    def contextMenuEvent(self, event):
        #todo: put something here
        pass

    def create_layout(self):
        self.main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.main_layout)

        if self.scroller:

            self.scroll_area = QtWidgets.QScrollArea()
            self.scroll_area.setWidgetResizable(True)
            self.main_layout.addWidget(self.scroll_area)
            self.scroll_widget = QtWidgets.QWidget()
            self.scroll_area.setWidget(self.scroll_widget)
            self.timestep_layout = QtWidgets.QHBoxLayout()
            self.scroll_widget.setLayout(self.timestep_layout)
        else:
            self.timestep_layout = QtWidgets.QHBoxLayout()
            self.main_layout.addLayout(self.timestep_layout)

    def remove_task(self):
        self.llci.remove_lltask(self.rightclicked_qtask.task, True)

    def create_task_inside(self, classname):
        self.llci.create_lltask(classname, self.rightclicked_qtask.task)

    def create_task_after(self, classname):
        self.llci.create_lltask(classname, self.task, self.rightclicked_qtask.task)

    def insert_task_after(self, classname):
        self.llci.create_lltask(classname, self.task, self.rightclicked_qtask.task, True)

    def clear_selection(self):
        if self.selected_qtask is not None:
            self.clear_dependences(self.selected_qtask)
            self.selected_qtask.set_selected(False)
            self.selected_qtask = None

    def qtask_clicked(self, qtask):
        # deselect an already selected qtask
        self.clear_selection()
        # store selected qtask, inform it its been selected
        self.selected_qtask = qtask
        qtask.set_selected(True)
        # draw parent connections
        self.show_dependences(qtask)

        self.task_selection_changed.emit(qtask.task)


    def qtask_rightclicked(self, qtask):

        self.rightclicked_qtask = qtask

        menu = QtWidgets.QMenu(self)
        menu.addMenu(self.create_task_inside_menu)
        menu.addMenu(self.create_task_after_menu)
        menu.addMenu(self.insert_task_after_menu)
        menu.addSeparator()

        if qtask==self.selected_qtask: # if we right clicked on the selected qtask
            act = menu.addAction("Move to start")
            act.triggered.connect(self.clear_task_dependences)
        elif self.selected_qtask is not None: #we right clicked on a different qtask, and we have actually selected something
            act = menu.addAction("Set as only dependence")
            act.triggered.connect(self.set_only_dependence)
            act = menu.addAction("Add to dependence list")
            act.triggered.connect(self.add_to_dependences)
        menu.addSeparator()

        menu.addAction("Refresh")
        menu.addAction("Reset + Refresh")
        menu.addSeparator()

        act = menu.addAction("Remove task")
        act.triggered.connect(self.remove_task)

        menu.exec_(QtGui.QCursor.pos())

    def clear_task_dependences(self):
        param =  self.rightclicked_qtask.task.get_parameter("Task Dependences")
        self.llci.set_parameter(param, [])

    def set_only_dependence(self):
        param = self.selected_qtask.task.get_parameter("Task Dependences")
        self.llci.set_parameter(param, [self.rightclicked_qtask.task,])

    def add_to_dependences(self):
        param = self.selected_qtask.task.get_parameter("Task Dependences")
        self.llci.set_parameter(param, param.value+[self.rightclicked_qtask.task, ])

    def qtask_doubleclicked(self, qtask):
        self.qtask_clicked(qtask)
        qtask.spawn_child_container()

    def show_dependences(self, qtask):
        for d in qtask.dependences:
            d.set_dependent_selected(True)

    def clear_dependences(self, qtask):
        for d in qtask.dependences:
            d.set_dependent_selected(False)

    def get_opened_path(self):
        if self.selected_qtask is None:
            return (None,)
        else:
            if self.selected_qtask.subtask_container is None:
                return (self.selected_qtask.task.ref_id,)
            else:
                return (self.selected_qtask.task.ref_id,) + self.selected_qtask.subtask_container.get_opened_path()

    def restore_selection(self, path):
        # find matching qtask
        found = False
        qtask = None
        for qtsk in self.qtasks:
            if qtsk.task.ref_id==path[0]:
                qtask = qtsk
                break
        if qtask is None:
            return
        self.qtask_clicked(qtask)
        if len(path)>1:
            qtask.spawn_child_container()
            if qtask.subtask_container is not None:
                qtask.subtask_container.restore_selection(path[1:])


    def update(self, task):
        # store current opened path
        current_path = self.get_opened_path()

        # clear current display
        # todo: check these are really being removed  from memory
        for qtask in self.qtasks:
            #qtask.destroyHierarchy() <- implement me
            qtask.setParent(None)
        count = self.timestep_layout.count()
        for i in range(count):
            item = self.timestep_layout.itemAt(0)
            self.timestep_layout.removeItem(item)

        self.task = task
        self.selected_qtask = None
        self.rightclicked_qtask = None

        if task is None:
            return

        # display tasks

        qtasks = [None]*len(task.ll_children)
        i=0
        # create task widget to wrap task objects
        for subtask in task.ll_children:
            subtask.temp_i = i #stores a variable in the object. it's bad practice but only way to run this algorithm fast.
            qtasks[i] = LLQtTaskWidget(self.llci, subtask, self)
            i=i+1

        # distribute dependence lists to each others widgets
        for qtask in qtasks:
            dependences = qtask.task["Task Dependences"]
            deps = [None]*len(dependences)
            i=0
            for subtask in dependences:
                deps[i] = qtasks[subtask.temp_i]
                i+=1
            qtask.dependences = deps

        # place them
        remaining_list = list(qtasks) # copy the list

        t = 0
        while(len(remaining_list)>0):

            placement_list = []
            remaining_list_new = []

            #find tasks to place
            for qtask in remaining_list:
                if qtask.check_dependences():
                    placement_list.append(qtask)
                else:
                    remaining_list_new.append(qtask)
            if len(placement_list)==0:
                print "hierarchy failure LLQtTaskContainerWidget.update()"
                placement_list = remaining_list
                remaining_list_new = []

            # place them
            timestep = LLQtTaskTimestepWidget(self.llci, t)
            for qtask in placement_list:
                qtask.placed = True
                timestep.addQTask(qtask)
            timestep.addStretch(0)
            self.timestep_layout.addWidget(timestep)

            # update the list of remaining tasks to place
            remaining_list = remaining_list_new
            t = t + 1

        self.qtasks = qtasks
        self.timestep_layout.addStretch(0)
        self.restore_selection(current_path)



class LLQtTaskTimestepWidget(QtWidgets.QWidget):
    def __init__(self, llci, t):
        super(LLQtTaskTimestepWidget, self).__init__()
        self.llci = llci
        self.t = t
        # self.setMinimumSize(50,300)
        self.task_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.task_layout)

    def addQTask(self, qtask):
        self.task_layout.addWidget(qtask)

    def addStretch(self, stretch=0):
        self.task_layout.addStretch(stretch)

class LLQtTaskWidget(QtWidgets.QGroupBox):
    def __init__(self, llci, task, container=None):
        super(LLQtTaskWidget, self).__init__()
        self.container = container
        self.llci = llci
        self.task = task
        self.placed = False
        self.dependences=None

        self.vbox = QtWidgets.QVBoxLayout()
        self.setLayout(self.vbox)
        self.vbox.addWidget(QtWidgets.QLabel(task.classname))
        self.subtask_container = None

        #self.normal_style = "background-color: darkgray; color: black; border: 1px solid gray; border-radius: 5px; margin-top: 0.5em; title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px;}"
        #self.highlight_style = "background-color: darkgray; color: black; border: 2px solid black; border-radius: 5px; margin-top: 0.5em; title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px;}"

        self.normal_style = "QGroupBox{ border: 1px solid gray}"
        self.highlight_style = "QGroupBox{ border: 2px solid gray}"
        self.selected_style = "QGroupBox{ border: 2px solid black}"
        self.dependent_style = "QGroupBox{ border: 2px dashed black}"

        self.setStyleSheet(self.normal_style)

        self.mouseover = False
        self.leftmousedown = False
        self.rightmousedown = False
        self.selected = False
        self.dep_selected = False


    def set_dependent_selected(self, dep_selected):
        self.dep_selected = dep_selected
        self.update_style()

    def check_dependences(self):
        for qtask in self.dependences:
            if not qtask.placed:
                return False
        return True

    def enterEvent(self, event):
        self.mouseover = True
        self.update_style()

    def leaveEvent(self, event):
        self.leftmousedown = False
        self.rightmousedown = False
        self.mouseover = False
        self.update_style()

    def mouseDoubleClickEvent(self, event):
        self.container.qtask_doubleclicked(self)

    def spawn_child_container(self):
        if self.subtask_container is not None or len(self.task.ll_children)==0:
            return
        self.subtask_container = LLQtTaskContainerWidget(self.llci)
        self.subtask_container.update(self.task)
        self.subtask_container.task_selection_changed.connect(self.container.task_selection_changed.emit)
        self.vbox.addWidget(self.subtask_container,1)

    def mousePressEvent(self, event):
        if event.button()==Qt.Qt.LeftButton:
            self.leftmousedown = True
            self.rightmousedown = False
        elif event.button()==Qt.Qt.RightButton:
            self.leftmousedown = False
            self.rightmousedown = True
        self.update_style()

    def mouseReleaseEvent(self, event):
        if self.container is not None:
            if self.leftmousedown:
                self.container.qtask_clicked(self)
            if self.rightmousedown:
                self.container.qtask_rightclicked(self)
        self.leftmousedown = False
        self.rightmousedown = False
        self.update_style()

    def set_selected(self, selected):
        if not selected and self.subtask_container is not None:
            self.subtask_container.clear_selection()
            #todo: properly dispose of subtask container
            self.subtask_container.hide()
            self.vbox.removeWidget(self.subtask_container)
            self.subtask_container = None
        self.selected = selected
        self.update_style()

    def update_style(self):
        if self.leftmousedown:
            self.setStyleSheet(self.selected_style)
        elif self.selected:
            self.setStyleSheet(self.selected_style)
        elif self.mouseover:
            self.setStyleSheet(self.highlight_style)
        elif self.dep_selected:
            self.setStyleSheet(self.dependent_style)
        else:
            self.setStyleSheet(self.normal_style)
