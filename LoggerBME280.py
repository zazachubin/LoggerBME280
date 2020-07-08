##!/usr/bin/env python3
from PyQt5.QtWidgets import (QMainWindow, QApplication, QLineEdit,
                             QLCDNumber, QWidget, QFileDialog, QMessageBox,
                             QPushButton, QAction, QComboBox, QVBoxLayout, 
                             QHBoxLayout, QLabel, QCheckBox, QDockWidget, QSizePolicy)
from PyQt5.QtGui import QIcon, QPalette, QColor, QDoubleValidator
from PyQt5.QtCore import QTime, Qt, QDir, QThread, pyqtSlot, pyqtSignal, QIODevice, QObject, QTimer, QTextStream
from PyQt5.QtSerialPort import QSerialPortInfo, QSerialPort
from datetime import datetime
from pprint import pprint
import pyqtgraph as pg
import platform
import random
import time
import json
import os
# ~~~~~~~~~~~~~~~~~~~~~~~~~ Custom QComboBox ~~~~~~~~~~~~~~~~~~~~~~~~~~
class ComboBox(QComboBox):
    popupAboutToBeShown = pyqtSignal()
# ++++++++++++++++++++++++++++ showPopup ++++++++++++++++++++++++++++++
    def showPopup(self):
        self.popupAboutToBeShown.emit()
        super(ComboBox, self).showPopup()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~ ReadDataThread ~~~~~~~~~~~~~~~~~~~~~~~~~~~
class ReadDataThread(QThread):
    change_value = pyqtSignal(float,float,float)
    def __init__(self, port, delay, parent=None):
        super(ReadDataThread, self).__init__()
        self._isRunning = True
        self.port = port
        self.Temperatura = 0
        self.Humidity = 0
        self.Pressure = 0

        self.delay = delay
        try:
            self.delay = int(float(self.delay)*1000)
        except ValueError:
            self.delay = int(float(self.delay.replace(",", "."))*1000)

    def run(self):
        if not self._isRunning:
            self._isRunning = True

        self.serPort = QSerialPort()
        self.serPort.setBaudRate(9600)
        self.serPort.setPortName(self.port)
        self.serPort.open(QIODevice.ReadWrite)
        self.serPort.readyRead.connect(self.dataReady)

        while self._isRunning == True:
            QThread.msleep(self.delay)
            if self.Temperatura != 0 and self.Humidity != 0 and self.Pressure != 0:
                self.change_value.emit(self.Temperatura,self.Humidity,self.Pressure)
            QApplication.processEvents()

    def dataReady(self):
        try:
            serial_object = str(self.serPort.readLine(), 'ascii')
            if ("$" in serial_object) and ("#" in serial_object):
                data = serial_object.split(',')
                self.Temperatura = float(data[0].split('$')[1])
                self.Humidity = float(data[1])
                self.Pressure = float(data[2].strip('\n').strip('\r').split('#')[0])
        except UnicodeDecodeError:
            pass
        

    def stop(self):
        self._isRunning = False
        self.serPort.close()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ App ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class App(QMainWindow):
# +++++++++++++++++++++++++++++__init__ +++++++++++++++++++++++++++++++
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon('img/logger.svg'))
        self.setWindowTitle('LoggerBME280')
        self.setGeometry(0, 0, 500, 500)
        self.config = { 'LogPath' : '',
                        'Port' : '',
                        'Delay' : 1
                        }
        self._alreadyRun = False
        self._pause = False
        self._stop = False

        self.initUI()
# +++++++++++++++++++++++++++++ initUI ++++++++++++++++++++++++++++++++
    def initUI(self):
        self.setStyleSheet("""QLCDNumber {  margin: 1px;
                                            padding: 7px;
                                            background-color: rgba(100,255,255,20);
                                            color: rgb(255,255,255);
                                            border-style: solid;
                                            border-radius: 8px;
                                            border-width: 3px;
                                            border-color: rgba(0,140,255,255);}
                              QDockWidget::title {text-align: center;}""")
        self.center()
################################ Menu #################################
        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('File')
        toolsMenu = mainMenu.addMenu('Tools')
        helpMenu = mainMenu.addMenu('Help')

        exitButton = QAction(QIcon('img/close.svg'), 'Exit', self)
        exitButton.setShortcut('Ctrl+Q')
        exitButton.setStatusTip('Exit application')
        exitButton.triggered.connect(self.close)
        fileMenu.addAction(exitButton)

        exportConfig = QAction(QIcon('img/config.svg'), 'save configs', self)
        fileMenu.addAction(exportConfig)
        exportConfig.triggered.connect(self.exportConfig)

        aboutButton = QAction(QIcon('img/info.svg'), 'About', self)
        aboutButton.triggered.connect(self.aboutDialog)
        helpMenu.addAction(aboutButton)
############################ File selector ############################
        self.chooseFile = QPushButton(QIcon('img/files.svg'),"Select File")
        self.chooseFile.clicked.connect(self.saveAs)
######################### Current path field ##########################
        self.selectedPath = QLineEdit()
        self.selectedPath.setAlignment(Qt.AlignCenter)
        self.selectedPath.setReadOnly(True)
        self.selectedPath.setToolTip("<h5>Current path")
############################### Delay #################################
        delayLabel = QLabel("Delay [s]")
        delayLabel.setMaximumHeight(20)

        validator = QDoubleValidator()
        self.delay = QLineEdit()
        self.delay.setAlignment(Qt.AlignCenter)
        self.delay.setValidator(validator)
########################### Port selector #############################
        PortSelectorLabel = QLabel("Port")
        PortSelectorLabel.setMaximumHeight(20)

        self.PortSelector = ComboBox()
        self.PortSelector.popupAboutToBeShown.connect(self.findPorts)

        VLayout_Delay_PortSelector_widgets = QVBoxLayout()
        VLayout_Delay_PortSelector_widgets.addWidget(self.PortSelector)
        VLayout_Delay_PortSelector_widgets.addWidget(self.delay)

        VLayout_Delay_PortSelector_labels = QVBoxLayout()
        VLayout_Delay_PortSelector_labels.addWidget(PortSelectorLabel)
        VLayout_Delay_PortSelector_labels.addWidget(delayLabel)

        hbox = QHBoxLayout()
        hbox.addLayout(VLayout_Delay_PortSelector_widgets)
        hbox.addLayout(VLayout_Delay_PortSelector_labels)
########################### Run-pause-stop ############################
        HLayout_Control = QHBoxLayout()

        run = QPushButton(QIcon('img/play.svg'),"Run")
        HLayout_Control.addWidget(run)
        run.clicked.connect(self.startDataPlotThread)

        pause = QPushButton(QIcon('img/pause.svg'),"Pause")
        HLayout_Control.addWidget(pause)
        pause.clicked.connect(self.pauseDataPlotThread)

        stop = QPushButton(QIcon('img/stop.svg'),"Stop")
        HLayout_Control.addWidget(stop)
        stop.clicked.connect(self.stopDataPlotThread)
############################ LCD displays #############################
        self.LCD_Temperature = QLCDNumber()
        self.LCD_Temperature.setDigitCount(9)

        self.LCD_Humidity = QLCDNumber()
        self.LCD_Humidity.setDigitCount(9)

        self.LCD_Pressure = QLCDNumber()
        self.LCD_Pressure.setDigitCount(9)

        LCD_Vlayout = QVBoxLayout()
        LCD_Vlayout.addWidget(self.LCD_Temperature)
        LCD_Vlayout.addWidget(self.LCD_Humidity)
        LCD_Vlayout.addWidget(self.LCD_Pressure)

        Label_Temperature = QLabel("C")
        Label_Humidity = QLabel("%")
        Label_Pressure = QLabel("Pa")
####################### Set widgets on layout #########################
        Label_Vlayout = QVBoxLayout()
        Label_Vlayout.addWidget(Label_Temperature)
        Label_Vlayout.addWidget(Label_Humidity)
        Label_Vlayout.addWidget(Label_Pressure)

        LCD_Hlayout = QHBoxLayout()
        LCD_Hlayout.addLayout(LCD_Vlayout,98)
        LCD_Hlayout.addLayout(Label_Vlayout,2)

        vLayout = QVBoxLayout()
        vLayout.addWidget(self.chooseFile)
        vLayout.addWidget(self.selectedPath)
        vLayout.addLayout(hbox)
        vLayout.addLayout(HLayout_Control)
        vLayout.addLayout(LCD_Hlayout)
################# Set control widgets on dockedWidget #################
        self.controlWidgets = QWidget()
        self.controlWidgets.setLayout(vLayout)
        self.controlDockWidget = QDockWidget('Control')
        self.controlDockWidget.setWidget(self.controlWidgets)
        self.addDockWidget(Qt.RightDockWidgetArea, self.controlDockWidget)

        self.loadConfigs()
        self.show()
# +++++++++++++++++++++++++++++ Center ++++++++++++++++++++++++++++++++
    def center(self):
        frameGm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())
# +++++++++++++++++++++ Start data plot thread ++++++++++++++++++++++++
    def startDataPlotThread(self):
        if self._alreadyRun != True or self._pause != False:
            self.thread = ReadDataThread(self.PortSelector.currentText(), self.delay.text())
            self.thread.change_value.connect(self.viewData)
            if self._pause != True:
                self.f = open(self._filePath,"w+")
                self.f.write("Time,Temperature[C],Humidity[%],Pressure[Pa]\n")
            self._pause = False
            self._alreadyRun = True
            self.thread.start()
# ++++++++++++++++++++++ Stop data plot thread ++++++++++++++++++++++++
    def stopDataPlotThread(self):
        self._alreadyRun = False
        self._pause = False
        self._stop = True
        self.thread.stop()
# +++++++++++++++++++++ Pause data plot thread ++++++++++++++++++++++++
    def pauseDataPlotThread(self):
        self._pause = True
        self.thread.stop()
# +++++++++++++++++++++++++++ View data +++++++++++++++++++++++++++++++
    def viewData(self,temperature,humidity,pressure):
        timestampStr = datetime.now().strftime('%d.%m.%Y %H:%M:%S.%f')

        self.LCD_Temperature.display("%.2f" % (temperature))
        self.LCD_Humidity.display("%.2f" % (humidity))
        self.LCD_Pressure.display("%.2f" % (pressure))

        self.f = open(self._filePath,"a+")
        self.f.write("{},".format(timestampStr) + "%.2f,%.2f,%.2f\n" % (temperature,humidity,pressure))
        self.f.close()
# +++++++++++++++++++++++++++++ Save ++++++++++++++++++++++++++++++++++
    def saveAs(self):
        saveAspath, _ = QFileDialog.getSaveFileName(self, 'Save as', QDir.homePath(), "TXT Files(*.txt)")
        if saveAspath != '':
            self._filePath = saveAspath
            self.selectedPath.setText(self._filePath)
# ++++++++++++++++++++++++++ About dialog +++++++++++++++++++++++++++++
    def aboutDialog(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("About")
        msg.setText("LoggerBME280")
        msg.setInformativeText("This is data logger based on sensor BME280 which generates logs with format:{Time, Temperature, Humidity, Pressure} created by Zaza Chubinidze Email : zazachubin@gmail.com")
        msg.exec_()
# +++++++++++++++++++++++++++++ Config ++++++++++++++++++++++++++++++++
    def exportConfig(self):
        configPath = "config.json"

        self.config['LogPath'] = self._filePath
        self.config['Port'] = self.PortSelector.currentText()
        self.config['Delay'] = self.delay.text()

        with open(configPath, 'w') as outfile:
            json.dump(self.config, outfile, indent=4)
# +++++++++++++++++++++++++++ Finde ports +++++++++++++++++++++++++++++
    def findPorts(self):
        port_list = QSerialPortInfo.availablePorts()
        port_list_names = []
        self.PortSelector.clear()
        for port in port_list:
            port_list_names.append(port.portName())
        self.PortSelector.addItems(port_list_names)
# +++++++++++++++++++++++++++ loadConfigs +++++++++++++++++++++++++++++
    def loadConfigs(self):
        configPath = "config.json"
        with open(configPath, 'r') as outfile:
            self.config = json.load(outfile)

        self._filePath = self.config['LogPath']
        self.PortSelector.addItem(self.config['Port'])
        self.delay.setText(self.config['Delay'])
        self.selectedPath.setText(self._filePath)


if __name__ == '__main__':
    app = QApplication([])
    app.setStyle('Fusion')

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)

    ex = App()
    app.exec_()