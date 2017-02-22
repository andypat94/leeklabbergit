import LeekLabber as LL
import PyQt5.QtCore as Qt
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets

import traceback

class LLQtExpSetupWidget(QtWidgets.QWidget):
    def __init__(self, llci):
        super(LLQtExpSetupWidget,self).__init__()
        self.mwcl_widgets=[]

        self.setWindowTitle("Experimental Setup")
        self.llci = llci
        self.llci.system_state_updated.connect(self.llci_update)

        #self.update()

        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.setLayout(self.main_layout)

        self.hbox = QtWidgets.QHBoxLayout()
        self.main_layout.addLayout(self.hbox)

        self.widg_layout = QtWidgets.QVBoxLayout()
        self.widg_layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.main_layout.addLayout(self.widg_layout)

        self.tab_widget = QtWidgets.QTabWidget()

        self.main_layout.addWidget(self.tab_widget)

        self.button_add_line = QtWidgets.QPushButton("Add Line")
        self.button_add_line.clicked.connect(self.button_add_line_clicked)
        self.hbox.addWidget(self.button_add_line)

        self.checkboxViewAll = QtWidgets.QCheckBox("View all lines together")

        self.viewall = False

        self.hbox.addWidget(self.checkboxViewAll)
        self.checkboxViewAll.toggled.connect(self.checkboxViewAllToggled)
        self.checkboxViewAll.setChecked(self.viewall)

    def hideEvent(self,event): #todo: remove this.
        QtWidgets.QApplication.quit()

    def button_add_line_clicked(self):
        self.llci.create_llobject('LLMicrowaveControlLine', self.llci.state_exp_setup)

    def checkboxViewAllToggled(self, viewall):
        self.recreate_widgets(viewall)
        self.viewall = viewall

    def recreate_widgets(self, viewall=None):
        if viewall is None:
            viewall = self.viewall

        viewchange = viewall != self.viewall
        self.tab_widget.setVisible(not viewall)

        exp_setup = self.llci.state_exp_setup

        if exp_setup is None:
            return

        mwcls = exp_setup["Microwave Control Lines"]
        self.lines = len(mwcls)
        self.mwcls = mwcls

        if viewall:
            # move from tabs to page
            count = self.tab_widget.count()
            for i in range(count):
                widg = self.tab_widget.widget(0)
                self.tab_widget.removeTab(0)
                self.widg_layout.addWidget(widg)
                widg.show()
        else:
            # move from page to tabs
            count = self.widg_layout.count()
            for i in range(count):
                item = self.widg_layout.itemAt(0)
                widg = item.widget()
                self.widg_layout.removeItem(item)
                self.tab_widget.addTab(widg, str(self.tab_widget.count()+1))

        # delete some if we have too many
        while len(self.mwcl_widgets) > self.lines:
            if viewall:
                #remove last from page
                self.widg_layout.removeItem(self.widg_layout.count()-1)
            else:
                #remove last from tab
                self.tab_widget.removeTab(self.tab_widget.count()-1)

            del self.mwcl_widgets[-1]

        # add some if we don't have enough
        while len(self.mwcl_widgets) < self.lines:
            widg = LLQtMicrowaveControlLine(self.llci)
            self.mwcl_widgets.append(widg)
            if viewall:
                self.widg_layout.addWidget(widg)
            else:
                self.tab_widget.addTab(widg, str(self.tab_widget.count()+1))

        # give them all the latest ref
        for i in range(self.lines):
            self.mwcl_widgets[i].set_mwcl(self.mwcls[i])

    def llci_update(self):
        self.recreate_widgets()

class LLQtMicrowaveControlLine(QtWidgets.QWidget):

    def __init__(self,llci):
        super(LLQtMicrowaveControlLine,self).__init__()
        self.min_y = 200
        self.llci = llci
        self.devicebox = 100
        self.deviceboxborder = 5
        self.textspace = 5
        self.arrowhead = 5
        self.final_x = 300.
        self.centre_y = 25.
        self.centre_x = 150.
        self.mixer_radius = 20.
        self.dr = self.mixer_radius/1.414
        self.i_y = self.centre_y - self.dr
        self.q_y = self.centre_y + self.dr
        self.input_x = self.centre_x - self.dr
        self.output_x = self.centre_x + self.dr
        self.i2_y = 7*self.centre_y - self.dr
        self.q2_y = 7*self.centre_y + self.dr
        self.numdrives = 0
        self.final_y = 0
        self.setMinimumSize(self.final_x,2*self.centre_y)
        self.rftext = []
        self.lotext = []
        self.dactext = []
        self.adctext = []
        self.drives = []
        self.devices = []

        self.device_rect = Qt.QRectF(0.,0.,0.,0.)
        self.drive_rects = []
        self.menu_selected_drive = None

        self.dac_menu_ch_i =QtWidgets.QMenu(self)
        self.dac_menu_ch_i.setTitle("Channel I")
        self.dac_menu_ch_q =QtWidgets.QMenu(self)
        self.dac_menu_ch_q.setTitle("Channel Q")
        self.adc_menu_ch_i =QtWidgets.QMenu(self)
        self.adc_menu_ch_i.setTitle("Channel I")
        self.adc_menu_ch_q =QtWidgets.QMenu(self)
        self.adc_menu_ch_q.setTitle("Channel Q")

        self.dac_menu = QtWidgets.QMenu(self)
        self.dac_menu.setTitle("Change DACs..")
        self.act_change_dac_data = self.dac_menu.addAction("Data")
        self.dac_menu.addMenu(self.dac_menu_ch_i)
        self.dac_menu.addMenu(self.dac_menu_ch_q)
        self.act_change_dac_data.triggered.connect(self.change_dac_data)
        self.adc_menu = QtWidgets.QMenu(self)
        self.adc_menu.setTitle("Change ADCs..")
        self.act_change_adc_data = self.adc_menu.addAction("Data")
        self.adc_menu.addMenu(self.adc_menu_ch_i)
        self.adc_menu.addMenu(self.adc_menu_ch_q)
        self.act_change_adc_data.triggered.connect(self.change_adc_data)
        self.gen_menu = QtWidgets.QMenu(self)
        self.gen_menu.setTitle("Change Generators..")
        self.act_change_drive_gen = self.gen_menu.addAction("Drive")
        self.act_change_readout_gen = self.gen_menu.addAction("Readout")
        self.act_change_drive_gen.triggered.connect(self.change_drive_gen)
        self.act_change_readout_gen.triggered.connect(self.change_readout_gen)

    def contextMenuEvent(self, event):
        self.menu = QtWidgets.QMenu(self)
        i=0
        within_drive = False
        for drive_rect in self.drive_rects:
            if drive_rect.contains(event.pos()):
                within_drive = True
                self.menu_selected_drive = self.drives[i]
                self.menu.addMenu(self.dac_menu)
                self.menu.addMenu(self.adc_menu)
                self.menu.addMenu(self.gen_menu)
                for menu in (self.adc_menu_ch_i,self.adc_menu_ch_q,self.dac_menu_ch_i,self.dac_menu_ch_q):
                    menu.clear()
                dac_data = self.menu_selected_drive["DAC Data"]
                if dac_data is None:
                    num_dac_channels=0
                else:
                    num_dac_channels=dac_data.value.shape[0]
                adc_data = self.menu_selected_drive["ADC Data"]
                if adc_data is None:
                    num_adc_channels=0
                else:
                    num_adc_channels=adc_data.value.shape[0]
                for c in range(num_dac_channels):
                    ai=self.dac_menu_ch_i.addAction(str(c))
                    aq=self.dac_menu_ch_q.addAction(str(c))
                    ai.triggered.connect((lambda ch=c: lambda: self.change_dac_ch_i(ch))())
                    aq.triggered.connect((lambda ch=c: lambda: self.change_dac_ch_q(ch))())
                for c in range(num_adc_channels):
                    ai=self.adc_menu_ch_i.addAction(str(c))
                    aq=self.adc_menu_ch_q.addAction(str(c))
                    ai.triggered.connect((lambda ch=c: lambda: self.change_adc_ch_i(ch))())
                    aq.triggered.connect((lambda ch=c: lambda: self.change_adc_ch_q(ch))())
                break
            i+=1
        if within_drive:
            self.actRemoveDrive = self.menu.addAction("Remove Drive")
            self.actRemoveDrive.triggered.connect(self.remove_drive)
        self.menu.addSeparator()
        self.actAddDrive = self.menu.addAction("Add Drive")
        self.actAddDrive.triggered.connect(self.add_drive)
        self.act_change_devices = self.menu.addAction("Change Devices..")
        self.act_change_devices.triggered.connect(self.change_devices)
        self.actRemoveLine = self.menu.addAction("Remove Line")
        self.actRemoveLine.triggered.connect(self.remove_line)
        self.menu.popup(event.globalPos())


    def remove_line(self):
        self.llci.remove_llobject(self.mwcl)

    def add_drive(self):
        self.llci.create_llobject('LLDrive',self.mwcl)

    def remove_drive(self):
        self.llci.remove_llobject(self.menu_selected_drive)

    def change_dac_data(self):
        dialog = LL.LLQtSelectionDialog(False,False)
        dialog.set_parameter_filter((LL.LLObjectParameter.PTYPE_NUMPY,))
        dialog.set_objects(self.llci.state_instruments, "Instrument Name")
        dialog.set_selected_parameter(self.menu_selected_drive["DAC Data"])
        dialog.exec_()
        if dialog.result()==QtWidgets.QDialog.Accepted:
            print dialog.selected_item
            self.llci.set_parameter(self.menu_selected_drive.get_parameter("DAC Data"), dialog.selected_item)

    def change_dac_ch_i(self,ch):
        self.llci.set_parameter(self.menu_selected_drive.get_parameter("DAC I Channel"), ch)

    def change_dac_ch_q(self,ch):
        self.llci.set_parameter(self.menu_selected_drive.get_parameter("DAC Q Channel"), ch)

    def change_adc_data(self):
        dialog = LL.LLQtSelectionDialog(False,False)
        dialog.set_parameter_filter((LL.LLObjectParameter.PTYPE_NUMPY,))
        dialog.set_objects(self.llci.state_instruments, "Instrument Name")
        dialog.set_selected_parameter(self.menu_selected_drive["ADC Data"])
        dialog.exec_()
        if dialog.result()==QtWidgets.QDialog.Accepted:
            print dialog.selected_item
            self.llci.set_parameter(self.menu_selected_drive.get_parameter("ADC Data"), dialog.selected_item)

    def change_adc_ch_i(self,ch):
        self.llci.set_parameter(self.menu_selected_drive.get_parameter("ADC I Channel"), ch)

    def change_adc_ch_q(self,ch):
        self.llci.set_parameter(self.menu_selected_drive.get_parameter("ADC Q Channel"), ch)

    def change_drive_gen(self):
        dialog = LL.LLQtSelectionDialog(True,False)
        dialog.set_objects(self.llci.state_instruments, "Instrument Name")
        dialog.set_selected_object(self.menu_selected_drive["Drive Generator"])
        dialog.exec_()
        if dialog.result()==QtWidgets.QDialog.Accepted:
            self.llci.set_parameter(self.menu_selected_drive.get_parameter("Drive Generator"), dialog.selected_item)

    def change_readout_gen(self):
        dialog = LL.LLQtSelectionDialog(True, False)
        dialog.set_objects(self.llci.state_instruments, "Instrument Name")
        dialog.set_selected_object(self.menu_selected_drive["Readout Generator"])
        dialog.exec_()
        if dialog.result() == QtWidgets.QDialog.Accepted:
            self.llci.set_parameter(self.menu_selected_drive.get_parameter("Readout Generator"), dialog.selected_item)

    def change_devices(self):
        dialog = LL.LLQtSelectionDialog(True,True)
        dialog.set_objects(self.llci.state_devices, "Device Name")
        dialog.set_selected_objects(self.devices)
        dialog.exec_()
        if dialog.result()==QtWidgets.QDialog.Accepted:
            self.llci.set_parameter(self.mwcl.get_parameter("Connected Devices"), dialog.selected_items)

    def set_mwcl(self, mwcl):
        self.mwcl =  mwcl
        self.drives = mwcl["Microwave Drives"]
        self.devices = mwcl["Connected Devices"]
        numdrives = len(self.drives)
        numdevices = len(self.devices)

        # do  stuff
        del self.rftext[:]
        del self.lotext[:]
        del self.dactext[:]
        del self.adctext[:]
        for drive in self.drives:

            drivegen = drive["Drive Generator"]
            if drivegen is None:
                rfname = "None"
            else:
                rfname = drivegen["Instrument Name"]

            readoutgen = drive["Readout Generator"]
            if readoutgen is None:
                loname = "None"
            else:
                loname = readoutgen["Instrument Name"]

            if drive["Planned"]:
                freqtxt = "%.4f GHz" % (drive["Plan Frequency"]/1e9)
                powtxt = "%.2f dBm" % (drive["Plan Power"])
                self.rftext.append(rfname + "\n" + freqtxt + "\n" + powtxt)
                self.lotext.append(loname + "\n" + freqtxt + "\n16 dBm")
            else:
                self.rftext.append(rfname + "\n\n")
                self.lotext.append(loname + "\n\n")

            dacdata = drive["DAC Data"]
            if dacdata is None:
                self.dactext.append("None")
            else:
                self.dactext.append("%s\n%s\nI:CH%i, Q:CH%i" % (dacdata.obj_ref["Instrument Name"], dacdata.label, drive["DAC I Channel"],drive["DAC Q Channel"]))

            adcdata = drive["ADC Data"]
            if adcdata is None:
                self.adctext.append("None")
            else:
                self.adctext.append("%s\n%s\nI:CH%i, Q:CH%i" % (adcdata.obj_ref["Instrument Name"], adcdata.label, drive["ADC I Channel"],drive["ADC Q Channel"]))

        self.deviceboxtext = "Devices: \n\n"
        for device  in  self.devices:
            self.deviceboxtext += device["Device Name"] + "\n"

        self.numdrives = numdrives
        self.numdevices = numdevices

        self.drive_rects = [Qt.QRectF(0.,0.,0.,0.)]*self.numdrives

        self.repaint()

    def paintEvent(self, event):

        painter = QtGui.QPainter(self)
        pen = QtGui.QPen(Qt.Qt.black)
        pendisable = QtGui.QPen(Qt.Qt.gray)
        pen.setWidth(2)
        pendisable.setWidth(2)
        painter.setPen(pen)

        y = 0
        for i in reversed(range(self.numdrives)):
            newy = self.draw_drive(painter, pen,pendisable, y, self.drives[i],self.rftext[i],self.lotext[i],self.dactext[i],self.adctext[i])
            self.drive_rects[i] = Qt.QRectF(0,y,self.final_x,newy-y)
            y = newy
        self.final_y = y
        if self.final_y < self.min_y:
            self.final_y = self.min_y

        self.device_rect = Qt.QRectF(self.final_x,self.deviceboxborder,self.devicebox-self.deviceboxborder,self.final_y-2*self.deviceboxborder)
        painter.drawRect(self.device_rect)
        devicetextrect = Qt.QRectF(self.final_x+self.deviceboxborder,self.deviceboxborder,self.devicebox-2*self.deviceboxborder,self.final_y-2*self.deviceboxborder)
        painter.drawText(devicetextrect,Qt.Qt.AlignLeft | Qt.Qt.AlignVCenter,self.deviceboxtext)

        self.setMinimumSize(self.final_x+self.devicebox,self.final_y)

    def draw_drive(self,painter,pen,pendisable,yoffset,drive,rftext,lotext,dactext,adctext):


        # draw UC mixer + DAC lines
        if drive["Plan Modulated"]:
            painter.setPen(pen)
        else:
            painter.setPen(pendisable)
        painter.drawLine(0,yoffset+self.i_y,self.input_x,yoffset+self.i_y)
        painter.drawLine(0,yoffset+self.q_y,self.input_x,yoffset+self.q_y)
        painter.drawLine(self.input_x,yoffset+self.i_y,self.output_x,yoffset+self.q_y)
        painter.drawLine(self.input_x,yoffset+self.q_y,self.output_x,yoffset+self.i_y)
        painter.drawEllipse(Qt.QRectF(self.centre_x-self.mixer_radius,yoffset+self.centre_y-self.mixer_radius,2*self.mixer_radius,2*self.mixer_radius))
        painter.setPen(pen)

        #draw uc mixer -> fridge
        painter.drawLine(self.centre_x+self.mixer_radius, yoffset+self.centre_y, self.final_x, yoffset+self.centre_y)
        painter.drawLine(self.final_x-self.arrowhead, yoffset+self.centre_y-self.arrowhead, self.final_x, yoffset+self.centre_y)
        painter.drawLine(self.final_x-self.arrowhead, yoffset+self.centre_y+self.arrowhead, self.final_x, yoffset+self.centre_y)

        #draw RF sig -> UC mixer
        painter.drawLine(self.centre_x,yoffset+self.centre_y+self.mixer_radius,self.centre_x,yoffset+3*self.centre_y-self.mixer_radius)

        #draw RF sig
        painter.drawEllipse(Qt.QRectF(self.centre_x - self.mixer_radius, yoffset+3*self.centre_y - self.mixer_radius, 2 * self.mixer_radius,2 * self.mixer_radius))
        painter.drawArc(Qt.QRectF(self.centre_x - self.mixer_radius/2., yoffset+3*self.centre_y - self.mixer_radius/2, self.mixer_radius/2., self.mixer_radius),0,180*16)
        painter.drawArc(Qt.QRectF(self.centre_x, yoffset+3*self.centre_y - self.mixer_radius/2, self.mixer_radius/2., self.mixer_radius),180*16,180*16)

        # draw RF text
        textRect = Qt.QRectF(self.centre_x+self.mixer_radius+self.textspace, yoffset + 2*self.centre_y, self.final_x-self.centre_x, 2*self.centre_y)
        painter.drawText(textRect,Qt.Qt.AlignLeft | Qt.Qt.AlignVCenter, rftext)

        # draw DAC text
        textRect = Qt.QRectF(0,yoffset+self.q_y, self.centre_x, 3*self.centre_y-self.dr)
        painter.drawText(textRect,Qt.Qt.AlignLeft | Qt.Qt.AlignTop, dactext)

        if(drive["Readout Capable"]):

            # draw LO sig
            painter.drawEllipse(Qt.QRectF(self.centre_x - self.mixer_radius, yoffset+5 * self.centre_y - self.mixer_radius, 2 * self.mixer_radius,2 * self.mixer_radius))
            painter.drawArc(Qt.QRectF(self.centre_x - self.mixer_radius / 2., yoffset+5 * self.centre_y - self.mixer_radius / 2, self.mixer_radius / 2., self.mixer_radius), 0, 180 * 16)
            painter.drawArc(Qt.QRectF(self.centre_x, yoffset+5 * self.centre_y - self.mixer_radius / 2, self.mixer_radius / 2., self.mixer_radius),180 * 16, 180 * 16)

            #draw LO text
            textRect = Qt.QRectF(self.centre_x + self.mixer_radius + self.textspace, yoffset + 4 * self.centre_y,
                                 self.final_x - self.centre_x, 2 * self.centre_y)
            painter.drawText(textRect, Qt.Qt.AlignLeft | Qt.Qt.AlignVCenter, lotext)

            #draw LO sig -> DC mixer
            painter.drawLine(self.centre_x,yoffset+5*self.centre_y+self.mixer_radius,self.centre_x,yoffset+7*self.centre_y-self.mixer_radius)

            # draw DC mixer
            painter.drawLine(self.input_x,yoffset+self.i2_y,self.output_x,yoffset+self.q2_y)
            painter.drawLine(self.input_x,yoffset+self.q2_y,self.output_x,yoffset+self.i2_y)
            painter.drawEllipse(Qt.QRectF(self.centre_x-self.mixer_radius,yoffset+7*self.centre_y-self.mixer_radius,2*self.mixer_radius,2*self.mixer_radius))

            #draw fridge->dc mixer
            painter.drawLine(self.centre_x + self.mixer_radius, yoffset + 7*self.centre_y, self.final_x,
                             yoffset + 7*self.centre_y)
            painter.drawLine(self.centre_x + self.mixer_radius + self.arrowhead, yoffset + 7*self.centre_y - self.arrowhead, self.centre_x + self.mixer_radius,
                             yoffset + 7*self.centre_y)
            painter.drawLine(self.centre_x + self.mixer_radius + self.arrowhead, yoffset + 7*self.centre_y + self.arrowhead, self.centre_x + self.mixer_radius,
                             yoffset + 7*self.centre_y)

            # draw ADC lines
            painter.drawLine(0,yoffset+self.i2_y,self.input_x,yoffset+self.i2_y)
            painter.drawLine(0,yoffset+self.q2_y,self.input_x,yoffset+self.q2_y)

            # draw ADC text
            textRect = Qt.QRectF(0, yoffset + 4*self.centre_y - 1, self.centre_x, 3 * self.centre_y - self.dr)
            painter.drawText(textRect, Qt.Qt.AlignLeft | Qt.Qt.AlignBottom, adctext)

            return yoffset  + 8*self.centre_y

        else:
            return yoffset + 4*self.centre_y


