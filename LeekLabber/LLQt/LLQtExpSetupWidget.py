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

        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.setLayout(self.main_layout)

        self.widg_layout = QtWidgets.QVBoxLayout()
        self.widg_layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.main_layout.addLayout(self.widg_layout)

        self.tab_widget = QtWidgets.QTabWidget()
        #self.tab_widget.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.main_layout.addWidget(self.tab_widget)

        self.checkboxViewAll = QtWidgets.QCheckBox("View all lines together")

        self.viewall = True
        self.mwcl_widgets=[]

        self.main_layout.addWidget(self.checkboxViewAll)
        self.checkboxViewAll.toggled.connect(self.checkboxViewAllToggled)
        self.checkboxViewAll.setChecked(self.viewall)


    def checkboxViewAllToggled(self, viewall):
        self.viewall = viewall
        if viewall:
            self.tab_widget.clear()
            self.tab_widget.hide()
            for widg in self.mwcl_widgets:
                self.widg_layout.addWidget(widg)
                widg.show()
        else:
            self.tab_widget.show()
            i=0
            for widg in self.mwcl_widgets:
                i+=1
                self.tab_widget.addTab(widg,str(i))


    def llci_update(self):

        # if self.llci.state_root is None or self.llci.state_root["Experiment Setups"] is None or len(self.llci.state_root.expsetups.ll_children)==0:
        #     return
        # exp_setup =  self.llci.state_root.expsetups.ll_children[0]
        # print ("Lines = " + str(len(exp_setup["Microwave Control Lines"])))

        exp_setup = self.llci.state_exp_setup

        if exp_setup is None:
            return

        mwcls = exp_setup["Microwave Control Lines"]
        lines = len(mwcls)

        while len(self.mwcl_widgets) < lines:
            widg = LLQtMicrowaveControlLine()
            self.mwcl_widgets.append(widg)
            if self.viewall:
                self.widg_layout.addWidget(widg)
            else:
                self.tab_widget.addTab(widg, str(self.tab_widget.count()+1))

        for i in range(lines):
            self.mwcl_widgets[i].set_mwcl(mwcls[i])



class LLQtMicrowaveControlLine(QtWidgets.QWidget):

    def __init__(self):
        super(LLQtMicrowaveControlLine,self).__init__()
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
            y = self.draw_drive(painter, pen,pendisable, y, self.drives[i],self.rftext[i],self.lotext[i],self.dactext[i],self.adctext[i])
        self.final_y = y

        devicerect = Qt.QRectF(self.final_x,self.deviceboxborder,self.devicebox-self.deviceboxborder,self.final_y-2*self.deviceboxborder)
        painter.drawRect(devicerect)
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


