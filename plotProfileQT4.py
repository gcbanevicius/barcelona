#!/usr/bin/env python

from __future__ import print_function

import random
import re
import sys

from PyQt4 import QtGui, QtCore

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from numpy import arange, sin, pi

import generateCallgraph



class MyPopup(QtGui.QWidget):
    def __init__(self, startTime, methodInfo):
        QtGui.QWidget.__init__(self)
        self.startTime = startTime
        self.methodInfo = methodInfo

    def paintEvent(self, e):
        labelStr = "Start time (ms): %s" % (str(self.startTime))
        #label = QtGui.QLabel(str(self.startTime), self)
        label = QtGui.QLabel(labelStr, self)
        label.show()

        #dc = QtGui.QPainter(self)
        #dc.drawLine(0, 0, 100, 100)
        #dc.drawLine(100, 0, 0, 100)

class MethodInfo:

    def __init__(self, startTime, endTime, avgPower):
        self.startTime = startTime
        self.endTime = endTime
        self.avgPower = avgPower

class MethodButton:

    def __init__(self, methodName, startTime, slider):
        self.methodName = methodName
        self.startTime = startTime
        self.slider = slider
        self.button = QtGui.QPushButton(self.methodName)
        self.button.setFlat(True)
        self.button.clicked.connect(self.onClicked)

    def getButton(self):
        return self.button

    def getSliderStart(self):
        return self.startTime/self.maxValue

    def onClicked(self):
        position = self.startTime / self.slider.maximum()
        print(self.startTime, position)
        self.slider.setValue(position)


class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""
    def __init__(self, parent=None, width=10, height=8, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        # We want the axes cleared every time plot() is called
        self.axes.hold(False)

        self.compute_initial_figure()

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        pass


class MyScrollingMplCanvas(MyMplCanvas):
    """This is the class for the scrolling plot"""

    MAX_PNTS = 1000

    def __init__(self, *args, **kwargs):
        
        super(MyScrollingMplCanvas, self).__init__(*args, **kwargs)
        self.times = []
        self.vals = []
        self.methNames = []

        with open('powerProfile.csv','r') as powerProfile:
            for line in powerProfile.readlines():
                line = line.split(',')
                self.times.append(line[0])
                self.vals.append(line[1])
                self.methNames.append(line[2])

        self.slider = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.slider.setRange(1,len(self.vals) - self.MAX_PNTS)
        self.slider.valueChanged[int].connect(self.changeSliderValue)
        self.maxPowerVal = float(max(self.vals))

        print(self.times[0], self.vals[0])
        l, = self.axes.plot(self.times[:self.MAX_PNTS], self.vals[:self.MAX_PNTS])
        self.axes.set_autoscalex_on(False)
        self.axes.set_xlim([0.0, self.MAX_PNTS*0.0002])
        self.axes.set_xlabel('Time (sec)')
        self.axes.set_ylim([0.0, self.maxPowerVal])
        self.axes.set_ylabel('Power (mW)')
        #print(type(self.axes))
        #print(type(self.axes).__name__)
        #self.axes.axvspan(100,5000,color="red")

    def getSlider(self):
        return self.slider

    def changeSliderValue(self, newStart):
        newEnd = newStart + self.MAX_PNTS
        l, = self.axes.plot(self.times[newStart:newEnd], self.vals[newStart:newEnd])
        self.axes.set_autoscalex_on(False)
        self.axes.set_xlim([newStart*0.0002,newEnd*0.0002])
        self.axes.set_xlabel('Time (sec)')
        self.axes.set_ylim([0.0, self.maxPowerVal])
        self.axes.set_ylabel('Power (mW)')
        self.draw()


class ApplicationWindow(QtGui.QWidget):
    def __init__(self):
        super(ApplicationWindow, self).__init__()

        # this is a mapping of method-name-buttons to relevant info
        self.buttonHash = {}

        # popup window for hover on button
        self.popup = None

        comm = """self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("application main window")

        self.file_menu = QtGui.QMenu('&File', self)
        self.file_menu.addAction('&Quit', self.fileQuit,
                                 QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)

        self.help_menu = QtGui.QMenu('&Help', self)
        self.menuBar().addSeparator()"""

        #self.main_widget = QtGui.QWidget(self)

        # create the graph and slider

        scrollWidget = QtGui.QWidget()
        textVBox = QtGui.QVBoxLayout()
        textVBox.addStretch(1)

        #self.addMethodNames(textVBox)


        graphVBox = QtGui.QVBoxLayout()
        graphVBox.addStretch(1)

        myGraph = MyScrollingMplCanvas()
        #myGraph.axes.axvspan(0, 5000, facecolor="red", alpha=0.5)
        myGraph.draw()

        self.slider = myGraph.getSlider()
        graphVBox.addWidget(myGraph)
        graphVBox.addWidget(self.slider)

        self.addMethodNames(textVBox)

        scrollWidget.setLayout(textVBox)
        scrollArea = QtGui.QScrollArea()
        scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scrollArea.setWidgetResizable(False)
        scrollArea.setWidget(scrollWidget)


        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(scrollArea)
        hbox.addLayout(graphVBox)

        self.setLayout(hbox)
        self.show()

    def adjustTime(self, time, startTime):
        time = time - startTime
        return time

    def addMethodNames(self, textVBox):
        comm = """times = []
        vals = []
        methNames = []
        
        with open('powerProfile.csv','r') as powerProfile:
            for line in powerProfile.readlines():
                line = line.split(',')
                times.append(line[0])
                vals.append(line[1])
                methNames.append(line[2])
                label = QtGui.QLabel(line[2], self)
                textVBox.addWidget(label)"""

        startTime = -1L
        tuples = []
        with open("Logger.txt", "r") as loggerFile:
            for line in loggerFile.readlines():
                line = line.strip()
                match = re.search('(Enter|Exit)\s(\S+).*?(\d+$)', line)

                direction = match.group(1)
                name = match.group(2)
                time = long(match.group(3))

                if startTime < 0:
                    startTime = time

                time = self.adjustTime(time, startTime)
 
                logTuple = (direction, name, time)
                tuples.append(logTuple)

        # get callstack and add buttons
        methodTups = generateCallgraph.parseAbsoluteTimes(tuples)
        print(self.slider.maximum())
        for methodTup in methodTups:
            #myButton = MethodButton(methodTup[1], methodTup[0], self.slider)
            #button = myButton.getButton()

            button = QtGui.QPushButton(methodTup[1])
            button.setFlat(True)
            hashVal = hash(button)
            #print(hashVal) # NB: should definitely check if entry already present
            if hashVal not in self.buttonHash:
                # NB!!! Fix these hash vals!!!
                print(methodTup)
                methodInfo = MethodInfo(methodTup[0], methodTup[0]+100, methodTup[2])
                self.buttonHash[hashVal] = methodTup[0]
            else:
                print("Argh... button was already in HashTable!", sys.stderr)
                sys.exit(1)

            startTime = methodTup[0]
            position = startTime * 5 # time is recorded in fifths of a millisecond

            #button.clicked.connect(self.onClicked(position))
            button.installEventFilter(self)
            #button.clicked.connect(myButton.onClicked)
            #myButton.button.clicked.connect(self.onClicked)
            #myButton.button.clicked.connect(f(position) )
            #textVBox.addWidget(myButton.button)
            textVBox.addWidget(button)

    def eventFilter(self, object, event):
        #print(object, type(object))

        if event.type() == QtCore.QEvent.MouseButtonPress:
            #if hash(object) in self.buttonHash:
            #    print("HOT DOG!")
            #print("Button press!")
            hashVal = hash(object) # the object is the button
            startTime = self.buttonHash[hashVal]
            position = startTime * 5 # time is recorded in fifths of a millisecond
            self.slider.setValue(position)
            return True

        #if event.type() == QtCore.QEvent.HoverEnter:
        if event.type() == QtCore.QEvent.MouseButtonDblClick:
            #print("Hover time!")
            hashVal = hash(object) # the object is the button
            startTime = self.buttonHash[hashVal]
            self.popup = MyPopup(startTime)
            ### oooo baby, it's all here!
            cursor = QtGui.QCursor()
            print(cursor.pos())
            x = cursor.pos().x()
            y = cursor.pos().y()
            print(x,y)
            self.popup.setGeometry(QtCore.QRect(x, y+50, 400, 200))
            self.popup.show()
            return True

        #if event.type() == QtCore.QEvent.HoverLeave:
        #    self.popup = None
        #    return True

        return False
            

    def onClicked(self, position):
        #position = self.startTime / self.slider.maximum()
        #print(self.startTime, position)

        #position = 100
        def doGoodStuff():
            print(position)
            self.slider.setValue(position)
        return doGoodStuff


    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()


if __name__ == "__main__":

    app = QtGui.QApplication(sys.argv)

    figure = Figure(figsize=(4,2), dpi=100)
    window = ApplicationWindow()

    try:
        window.show()
    except e:
        raise Exception("Oops, something went wrong: " + e.msg)
    app.exec_()

