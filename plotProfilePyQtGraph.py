#!/usr/bin/env python

from __future__ import print_function

import random
import re
import sys
import random

#from PyQt4 import QtGui, QtCore
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import pyqtgraph.widgets.MatplotlibWidget as MatplotlibWidget

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import numpy as np

import generateCallgraph


class ColorBlock:

    def __init__(self, color, startTime, endTime):
        self.color = color
        self.startTime = startTime
        self.endTime = endTime

    def printFields(self):
        print(self.color, self.startTime, self.endTime)

    def is_empty(self):
        if self.startTime == self.endTime:
            return True
        else:
             return False

class ColorBlockList:

    def __init__(self):
        self.colorBlockList = []

    def add(self, colorBlock):
        self.colorBlockList.append(colorBlock)

    def get(self, idx):
        return self.colorBlockList[idx]

    def length(self):
        return len(self.colorBlockList)

class MyPopup(QtGui.QWidget):
    def __init__(self, startTime, endTime, avgPower):
        QtGui.QWidget.__init__(self)
        self.startTime = startTime
        self.endTime = endTime
        self.avgPower = avgPower

    def paintEvent(self, e):
        labelStr = """
        Start time (ms): %s\n
        End time (ms): %s\n
        Average Power (mW): %s\n
        """ \
        % (str(self.startTime), str(self.endTime), str(self.avgPower))
        label = QtGui.QLabel(labelStr, self)
        label.show()

class MethodInfo:

    def __init__(self, methodName, startTime, endTime, avgPower):
        self.methodName = methodName
        self.startTime = startTime
        self.endTime = endTime
        self.avgPower = avgPower


class MyMplCanvas(FigureCanvas):

    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent=None, width=20, height=16, dpi=100):
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

    def __init__(self, plotItem, colorBlockList, colorMappings, *args, **kwargs):

        self.times = []
        self.vals = []
        self.methNames =[]
        self.colorBlockList = colorBlockList
        self.colorMappings = colorMappings
        super(MyScrollingMplCanvas, self).__init__(*args, **kwargs)

        with open('powerProfile.csv','r') as powerProfile:
            for line in powerProfile.readlines():
                line = line.split(',')
                self.times.append(line[0])
                self.vals.append(line[1])
                self.methNames.append(line[2])

        self.graphWidget = pg.PlotWidget()
        #self.graphWidget = pg.PlotItem()
        x = np.array(self.times, dtype='float_')
        y = np.array(self.vals, dtype='float_')
        #self.graphWidget.plot(x, y, pen='b')
        plotItem.plot(x, y, pen='b')

        comm = """self.mw = MatplotlibWidget.MatplotlibWidget()
        subplot = self.mw.getFigure().add_subplot(111)
        subplot.plot(self.times, self.vals)
        self.mw.draw()
        
        self.mw.slider = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.mw.slider.setRange(1,len(self.vals) - self.MAX_PNTS)
        self.mw.slider.valueChanged[int].connect(self.changeSliderValue)
        self.mw.maxPowerVal = float(max(self.vals))"""

        #l, = self.axes.plot(self.times[:self.MAX_PNTS], self.vals[:self.MAX_PNTS])
        self.axes.set_autoscalex_on(False)
        #self.axes.set_xlim([0.0, self.MAX_PNTS*0.0002])
        self.axes.set_xlabel('Time (sec)')
        #self.axes.set_ylim([0.0, self.maxPowerVal])
        self.axes.set_ylabel('Power (mW)')
        self.drawMethodRects(0)

        #print(type(self.graphWidget.axes))


    def changeSliderValue(self, newStart):
        newEnd = newStart + self.MAX_PNTS
        l, = self.axes.plot(self.times[newStart:newEnd], self.vals[newStart:newEnd])
        self.axes.set_autoscalex_on(False)
        self.axes.set_xlim([newStart*0.0002,newEnd*0.0002])
        self.axes.set_xlabel('Time (sec)')
        self.axes.set_ylim([0.0, self.maxPowerVal])
        self.axes.set_ylabel('Power (mW)')
        self.drawMethodRects(newStart)
        self.draw_idle()

    def drawMethodRects(self, startVal):
        #return True
        # lolol

        colorBlockIdx = self.colorMappings[startVal]
        colorBlock = self.colorBlockList.get(colorBlockIdx)

        colorBlock.printFields()
        
        # times are in msec, so divide by 1000 to get seconds
        startPos = colorBlock.startTime/1000
        endPos = min(colorBlock.endTime/1000, len(self.vals))
        self.axes.axvspan(startPos, endPos, ymin=0, ymax=0.05, \
                          facecolor=colorBlock.color, alpha=0.5)

        #return True
        # lolol
        
        maxPos = startPos + self.MAX_PNTS
        while endPos < maxPos:
            colorBlockIdx += 1
            colorBlock = self.colorBlockList.get(colorBlockIdx)
            endPos = min(colorBlock.endTime/1000, len(self.vals))
            #print(endPos, "!!!")
            self.axes.axvspan(colorBlock.startTime/1000.0, endPos, ymin=0, ymax=0.05, \
                              facecolor=colorBlock.color, alpha=0.5)
       


class ApplicationWindow(QtGui.QWidget):
    def __init__(self):
        super(ApplicationWindow, self).__init__()

        # this is a mapping of method-name-buttons to relevant info
        self.buttonHash = {}

        # popup window for hover on button
        self.popup = None

        # create the graph and slider
        scrollWidget = QtGui.QWidget()
        textVBox = QtGui.QVBoxLayout()
        textVBox.addStretch(1)

        # read in info, generate and use callgraph
        if (len(sys.argv) > 1):
            fileName = sys.argv[1]
        else:
            fileName = "Logger.txt"
        tuples = generateCallgraph.parseInputFile(fileName)
        self.methodTups = generateCallgraph.parseAbsoluteTimes(tuples)

        # this is the super fun part where we create the color scheme!
        self.colorBlockList = ColorBlockList()
        colors = ['red', 'green', 'blue', 'yellow' ]

        self.colorHash = {
            'red': QtCore.Qt.red,
            'green': QtCore.Qt.green,
            'blue': QtCore.Qt.blue,
            'yellow': QtCore.Qt.yellow,
        }

        mod = len(colors)
        i = 0
        for methodTup in self.methodTups:
            print(methodTup)
            colorBlock = ColorBlock(colors[i], methodTup[1], methodTup[2])
            if not colorBlock.is_empty():
                colorBlock.printFields()
                self.colorBlockList.add(colorBlock)
                i = (i+1) % mod 

        ### Actual layout work begins ###
        pg.setConfigOption('background', 'w')
        self.view = pg.GraphicsView()
        gl = pg.GraphicsLayout()
        self.view.setCentralItem(gl)
        self.view.show()
        # resize it
        #self.view.resize(800, 600)

        colorMappings = self.createColorMappings(self.colorBlockList)

        self.addMethodNames(textVBox, colorMappings)
        scrollWidget.setLayout(textVBox)
        scrollArea = pg.QtGui.QScrollArea()
        scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scrollArea.setWidgetResizable(False)
        #scrollArea.setMinimumWidth(300)
        #scrollArea.setMinimumHeight(800)
        scrollArea.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Expanding)
        scrollArea.setWidget(scrollWidget)

        gl.nextRow()
        proxyWdg = pg.QtGui.QGraphicsProxyWidget()
        #vb1 = pg.ViewBox()
        #gl.addItem(scrollWidget)
        #gl.addItem(vb1)
        proxyWdg.setWidget(scrollArea)
        gl.addItem(proxyWdg)

        self.p1 = gl.addPlot()
        self.p1.setMouseEnabled(y=False)
        self.p1.setXRange(.01, 0.04)
        myGraph = MyScrollingMplCanvas(self.p1, self.colorBlockList, colorMappings)
        #p1 = gl.addPlot(title="Plot 1")
        
        comm = """graphVBox = QtGui.QVBoxLayout()
        pg.setConfigOption('background', 'w')

        viewBox = pg.ViewBox()
        #viewBox.l

        myGraph = MyScrollingMplCanvas(colorBlockList=self.colorBlockList)
        #myGraph.graphWidget.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        myGraph.graphWidget.setMinimumWidth(1200)
        myGraph.graphWidget.setMinimumHeight(800)
        #graphVBox.addWidget(myGraph.slider)

        graphVBox.addWidget(myGraph.graphWidget)
        #graphVBox.addItem(myGraph.graphWidget)
        #graphVBox.addWidget(myGraph.mw)
        
        self.addMethodNames(textVBox, myGraph.colorMappings)
        scrollWidget.setLayout(textVBox)
        scrollArea = QtGui.QScrollArea()
        scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scrollArea.setWidgetResizable(False)
        scrollArea.setMinimumWidth(300)
        scrollArea.setMinimumHeight(800)
        #scrollArea.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        scrollArea.setWidget(scrollWidget)

        #hbox = QtGui.QGridLayout()
        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(0)
        hbox.addWidget(scrollArea)
        hbox.addStretch(1)
        #hbox.addWidget(myGraph.graphWidget)
        hbox.addLayout(graphVBox)

        self.setLayout(hbox)
        #self.setLayout(graphVBox)
        #self.show()
        """


    def addMethodNames(self, textVBox, colorMappings):

        # get callstack and add buttons
        prevDepth = -1
        prevParentList = []
        for methodTup in self.methodTups:
            container = QtGui.QHBoxLayout()
            button = QtGui.QPushButton(methodTup[0])
            button.setFocusPolicy(QtCore.Qt.NoFocus)
            #button.setFlat(True)
            button.setStyleSheet("""
                .QPushButton {
                    text-align: left;
                    padding: 5px
                }
            """)

            hashVal = hash(button)
            if hashVal not in self.buttonHash:
                # NB!!! Fix these hash vals!!!
                randval = random.randrange(1000, 5000)
                endTime = methodTup[1] + random.randrange(100,500)
                methodInfo = MethodInfo(methodTup[0], methodTup[1], endTime, randval)
                self.buttonHash[hashVal] = methodInfo
            else:
                print("Argh... button was already in HashTable!", sys.stderr)
                sys.exit(1)

            button.installEventFilter(self)

            # an ugly check... since we're using fake data in development
            if (methodTup[1] * 5) >= len(colorMappings):
                break

            colorIdx = int(methodTup[1] * 5) # LOVE this stuff...
            colorBlockIdx = colorMappings[colorIdx]
            colorBlock = self.colorBlockList.get(colorBlockIdx)
            colorName = colorBlock.color
            color = self.colorHash[colorName]

            # set color
            palette = QtGui.QPalette()
            palette.setColor(QtGui.QPalette.Background, self.colorHash[colorName])
            colorLabel = QtGui.QLabel("    ")
            colorLabel.setFixedSize(25, 25)
            colorLabel.setAutoFillBackground(True)
            colorLabel.setPalette(palette)

            # set indentation
            indent = " " * (4 * methodTup[3])
            #print((4*methodTup[3]), indent, "*")
            #indentLabel = QtGui.QLabel(indent)
            indentLabel = QtGui.QLabel(" ")
            indentLabel.setFixedSize(40*methodTup[3], 25)
            
            # hide children
            #if methodTup[3] != 0:
            #    indentLabel.setVisible(False)
            #    colorLabel.setVisible(False)
            #    button.setVisible(False)

            container.addWidget(indentLabel)
            container.addWidget(colorLabel)
            container.addWidget(button)
            textVBox.addLayout(container)

    def createColorMappings(self, colorBlockList):

        colorMappings = []
        colorBlockListLength = colorBlockList.length()
        colorBlockIdx = 0
        colorBlock = colorBlockList.get(colorBlockIdx)
        colorBlockEndTime = colorBlock.endTime
        with open('powerProfile.csv','r') as powerProfile:
            for line in powerProfile.readlines():
                line = line.split(',')
                time = float(line[0])*1000 # convert to msec
                if time < colorBlockEndTime:
                    colorMappings.append(colorBlockIdx)
                else:
                    colorBlockIdx += 1
                    colorBlock = colorBlockList.get(colorBlockIdx)
                    colorBlockEndTime = colorBlock.endTime
                    colorMappings.append(colorBlockIdx)

        return colorMappings


    def changeVisibility(self, object):

        visible = button.isVisible()
        object.setVisible(not visible)

    def eventFilter(self, object, event):

        if event.type() == QtCore.QEvent.MouseButtonPress:
            hashVal = hash(object) # the object is the button
            startTime = self.buttonHash[hashVal].startTime #[0]
            #position = startTime * 5 # time is recorded in fifths of a millisecond
            #self.slider.setValue(position)
            position = startTime / 1000
            self.p1.setXRange(position, position + 0.25)
            

            return True

        if event.type() == QtCore.QEvent.MouseButtonDblClick:
            hashVal = hash(object) # the object is the button
            methodInfo = self.buttonHash[hashVal]
            startTime = methodInfo.startTime
            endTime = methodInfo.endTime
            avgPower = methodInfo.avgPower
            self.popup = MyPopup(startTime, endTime, avgPower)
            ### oooo baby, it's all here!
            cursor = QtGui.QCursor()
            x = cursor.pos().x()
            y = cursor.pos().y()
            self.popup.setGeometry(QtCore.QRect(x, y+50, 400, 200))
            self.popup.show()

            # for now, double click will also display children

            return True

        return False
            

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()


if __name__ == "__main__":

    app = QtGui.QApplication(sys.argv)
    window = ApplicationWindow()

    try:
        window.view.show()
    except e:
        raise Exception("Oops, something went wrong: " + e.msg)
    app.exec_()

