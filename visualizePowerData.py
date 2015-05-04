#!/usr/bin/env python

from __future__ import print_function

import random
import re
import sys
import random
import time

from PySide import QtGui, QtCore
import pyqtgraph as pg
import numpy as np

import generateCallgraph

class ColorBlock:
    
    """Class with information about color-coded method rectangles"""

    def __init__(self, color, methodName, startTime, endTime, depth):
        self.color = color
        self.methodName = methodName
        self.startTime = startTime
        self.endTime = endTime
        self.depth = depth
        
        if self.endTime != float('inf'):
            self.xVals = np.array(range(int(self.startTime),int(self.endTime)+1))
        else:
            self.xVals = np.array(range(int(self.startTime), int(self.startTime)+100))
        self.yVals = np.array([0.5]*len(self.xVals))

    def printFields(self):
        print(self.color, self.startTime, self.endTime)

    def printFieldsCompare(self):
        print(self.color, self.startTime, self.endTime, self.xVals[0], self.xVals[-1])

    def printFieldsVerbose(self):
        print("Color is:", self.color, " | Start time:",  self.startTime, " | End time:", self.endTime)


class ColorBlockList:

    """A sequential list of all color blocks"""

    def __init__(self):
        self.colorBlockList = []

    def add(self, colorBlock):
        self.colorBlockList.append(colorBlock)

    def get(self, idx):
        return self.colorBlockList[idx]

    def length(self):
        return len(self.colorBlockList)


class MyPopup(QtGui.QWidget):

    """Class for popup window when you hit a method button"""

    def __init__(self, startTime, endTime):
        QtGui.QWidget.__init__(self)
        self.startTime = startTime
        self.endTime = endTime
        self.avgPower = avgPower

    def paintEvent(self, e):
        labelStr = """
        Start time (ms): %s\n
        End time (ms): %s\n
        """ \
        % (str(self.startTime), str(self.endTime))
        label = QtGui.QLabel(labelStr, self)
        label.show()

class MethodInfo:

    """Wraps relevant info about a method"""

    def __init__(self, methodName, startTime, endTime, depth):
        self.methodName = methodName
        self.startTime = startTime
        self.endTime = endTime
        self.depth = depth
        self.childrenList = []

    def addChild(self, child):
        self.childrenList.append(child)

    def printHelperCallgraph(self):
        myString = self.methodName + ": "
        for child in self.childrenList:
            myString += child.methodName + ", "
        print(myString)


class MyMethodButton(QtGui.QHBoxLayout):

    """Wraps consituent parts of a method button"""

    def __init__(self, indentLabel, colorLabel, button, *args, **kwargs):
        self.indentLabel = indentLabel
        self.colorLabel = colorLabel
        self.button = button
        super(MyMethodButton, self).__init__(*args, **kwargs)

        self.addWidget(indentLabel)
        self.addWidget(colorLabel)
        self.addWidget(button)


class MyMethodButtonPanel(QtGui.QVBoxLayout):

    """Vertical layout containing all method buttons""" 

    def __init__(self, appWindow, methodTups, colorBlockList, startTime, *args, **kwargs):
        self.appWindow = appWindow
        self.methodTups = methodTups
        self.colorBlockList = colorBlockList
        self.buttonList = []
        self.startTime = startTime

        self.colorHash = {
            'magenta': QtCore.Qt.magenta,
            'cyan': QtCore.Qt.cyan,
            'red': QtCore.Qt.red,
            'green': QtCore.Qt.green,
            'blue': QtCore.Qt.blue,
            'yellow': QtCore.Qt.yellow,
            'lightGray': QtCore.Qt.lightGray,
        }

        super(MyMethodButtonPanel, self).__init__(*args, **kwargs)
        
        # this is a mapping of method-name-buttons to relevant info
        self.buttonHash = {}
        self.addMethodNames()

    def addMethodNames(self):
        prevEndTime = -1
        for i in range(self.colorBlockList.length()):
            colorBlock = self.colorBlockList.get(i)
            if colorBlock.startTime < prevEndTime:
                continue

            if colorBlock.startTime > colorBlock.endTime:
                print("Color blocks times are out of order!")
                sys.exit(1)

            container = QtGui.QHBoxLayout()
            button = QtGui.QPushButton(colorBlock.methodName)
            button.setFocusPolicy(QtCore.Qt.NoFocus)
            button.setStyleSheet("""
                .QPushButton {
                    text-align: left;
                    padding: 5px
                }
            """)

            hashVal = hash(button)
            if hashVal not in self.buttonHash:
                methodInfo = MethodInfo(colorBlock.methodName, colorBlock.startTime, colorBlock.endTime, colorBlock.depth)
                self.buttonHash[hashVal] = methodInfo

            else:
                print("Error, button was already in HashTable!", sys.stderr)
                sys.exit(1)

            # add buttons to a list, to be referenced by eventFilter 
            # in the main ApplicationWindow class
            self.buttonList.append(button)

            # set color
            palette = QtGui.QPalette()
            colorName = colorBlock.color
            palette.setColor(QtGui.QPalette.Background, self.colorHash[colorName])
            colorLabel = QtGui.QLabel("    ")
            colorLabel.setFixedSize(25, 25)
            colorLabel.setAutoFillBackground(True)
            colorLabel.setPalette(palette)

            # set indentation
            depth = colorBlock.depth
            indent = " " * (4 * depth)
            indentLabel = QtGui.QLabel(" ")
            indentLabel.setFixedSize(40*depth, 25)
            
            # create button
            containerButton = MyMethodButton(indentLabel, colorLabel, button)
            self.addLayout(containerButton)
            prevEndTime = colorBlock.endTime

class MyPlot:

    """This is the class for the scrollable, zoomable plot"""


    def __init__(self, colorBlockList, startTime, windowSize, powerFile, *args, **kwargs):

        self.MAX_PNTS = 1000
        self.times = []
        self.vals = []
        self.powerFile = powerFile
        endTime = startTime+windowSize

        i = -1
        with open(self.powerFile,'r') as powerProfile:
            for line in powerProfile.readlines()[(startTime*5):(endTime*5)+1]:
                i += 1
                # the measurements are in fifths of a millisecond,
                # so only read every fifth one
                if (i % 5) != 0:
                    continue
                line = line.split(',')
                self.times.append(float(line[0]) * 1000.0) # convert to millisec
                self.vals.append(line[1])

        # get data for plotting
        self.x = np.array(self.times, dtype='float_')
        self.y = np.array(self.vals, dtype='float_')


class ApplicationWindow(QtGui.QWidget):
    def __init__(self, graphOnly=False):
        self.graphOnly = graphOnly

        # read in info, generate and use callgraph
        #if (len(sys.argv) > 1):
        #    fileName = sys.argv[1]
        #else:
        #    fileName = "Logger.txt"

        # check input files
        logFile = "Logger.txt"
        powerFile = "powerProfile.csv"
        for arg in sys.argv[1:]:
            if re.search('logfile=', arg):
                match = re.search('logfile=(.+)', arg)
                logFile = match.group(1)
            elif re.search('powerfile=', arg):
                match = re.search('powerfile=(.+)', arg)
                powerFile = match.group(1)

        # get the time range
        startTime = int(raw_input("Enter start time of the window (in milliseconds): "))
        self.windowSize = int(raw_input("Enter the size of the window (in milliseconds): "))

        #print("START:", time.time())

        # popup window for hover on button
        self.popup = None

        # store the callgraph as tuples, one per method
        tuples = generateCallgraph.parseInputFile(logFile, startTime, self.windowSize)
        self.methodTups = generateCallgraph.parseAbsoluteTimes(tuples, startTime, self.windowSize)

        # create the color scheme
        self.colorBlockList = ColorBlockList()
        self.createColorScheme()

        ### Actual layout work begins ###
        super(ApplicationWindow, self).__init__()
        pg.setConfigOption('background', 'w')
        self.view = pg.GraphicsView()
        gl = pg.GraphicsLayout()
        self.view.setCentralItem(gl)
        self.view.show()
        self.view.resize(1000, 600)

        ## Layout the method buttons 
        if not self.graphOnly:
            buttonVBox = MyMethodButtonPanel(self, self.methodTups, self.colorBlockList, startTime)
            scrollWidget = QtGui.QWidget()
            scrollWidget.setLayout(buttonVBox)

            self.buttonHash = buttonVBox.buttonHash
            for b in buttonVBox.buttonList:
                b.installEventFilter(self)

            scrollArea = QtGui.QScrollArea()
            scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
            scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
            scrollArea.setWidgetResizable(False)
            scrollArea.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Expanding)
            scrollArea.setWidget(scrollWidget)

            proxyScrollWidget = QtGui.QGraphicsProxyWidget()
            proxyScrollWidget.setWidget(scrollArea)
            gl.addItem(proxyScrollWidget)

        ## Layout the actual plot
        plotGl = gl.addLayout()
        
        # start with plot
        myPlot = MyPlot(self.colorBlockList, startTime, self.windowSize, powerFile)
        self.mainPlot = pg.PlotWidget(name='MainPlot', title='Application Instantaneous Power')
        self.mainPlot.setMouseEnabled(y=False)
        self.mainPlot.setXRange(0, 250)
        self.mainPlot.plot(myPlot.x, myPlot.y, pen='b')
        self.mainPlot.setLimits(xMin=startTime, xMax=startTime+self.windowSize)
        self.mainPlot.setLabel('bottom', text="Time (msec)")
        self.mainPlot.setLabel('left', text="Power (mW)")
        proxyMainWidget = QtGui.QGraphicsProxyWidget()
        proxyMainWidget.setWidget(self.mainPlot)
        plotGl.addItem(proxyMainWidget)

        ## now do method rectangles
        if not self.graphOnly:
            plotGl.nextRow()
            colorRectPlot = pg.PlotWidget(name='ColorRectPlot')
            colorRectPlot.hideAxis('bottom')
            colorRectPlot.hideButtons()
            colorRectPlot.setMouseEnabled(x=False, y=False)
            colorRectPlot.setXRange(0, 250)
            colorRectPlot.setXLink(self.mainPlot)
            colorRectPlot.setLimits(xMin=startTime, xMax=startTime+self.windowSize, yMin=0, yMax=1)
            colorRectPlot.setLabel('left', text=" ")

            self.drawMethodRects(colorRectPlot)

            proxyRectWidget = QtGui.QGraphicsProxyWidget()
            proxyRectWidget.setWidget(colorRectPlot)
            proxyRectWidget.setMaximumHeight(100)
            plotGl.addItem(proxyRectWidget)

    def createColorScheme(self):
        if not self.graphOnly:
            colors = ['red', 'green', 'blue', 'magenta', 'yellow', 'cyan']
            modVal = len(colors)
            i = 0
            for methodTup in self.methodTups:
                # no block for "zero-time" methods
                if not methodTup[1] == methodTup[2]:
                    if not methodTup[0] == "---":
                        color = colors[i]
                        i = (i+1) % modVal 
                    else:
                        color = 'lightGray'
                    colorBlock = ColorBlock(color, methodTup[0], methodTup[1], methodTup[2], methodTup[3])
                    self.colorBlockList.add(colorBlock)

    def drawMethodRects(self, plotItem):
        colorBlock = self.colorBlockList.get(0)
        colorPen = pg.mkPen(colorBlock.color[0], width=10)
        plotItem.plot(colorBlock.xVals, colorBlock.yVals, pen=colorPen)
        prevEndTime = colorBlock.endTime

        for i in range(1,self.colorBlockList.length()):
            colorBlock = self.colorBlockList.get(i)
            if colorBlock.startTime < prevEndTime:
                continue
            colorPen = pg.mkPen(colorBlock.color[0], width=10)
            plotItem.plot(colorBlock.xVals, colorBlock.yVals, pen=colorPen)
            prevEndTime = colorBlock.endTime
 
    def eventFilter(self, object, event):

        # left click jumps to x-value, right-click displays popup
        if event.type() == QtCore.QEvent.MouseButtonPress:
            if event.button() == QtCore.Qt.LeftButton:
                hashVal = hash(object) # the object is the button
                startTime = self.buttonHash[hashVal].startTime
                position = startTime
                self.mainPlot.setXRange(position, position+250)
                return True
            if event.button() == QtCore.Qt.RightButton:
                hashVal = hash(object) # the object is the button
                methodInfo = self.buttonHash[hashVal]
                startTime = methodInfo.startTime
                endTime = methodInfo.endTime
                self.popup = MyPopup(startTime, endTime)
                cursor = QtGui.QCursor()
                x = cursor.pos().x()
                y = cursor.pos().y()
                self.popup.setGeometry(QtCore.QRect(x, y+50, 400, 200))
                self.popup.show()
                return True

        return False

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()


if __name__ == "__main__":

    app = QtGui.QApplication(sys.argv)
    if "-go" in sys.argv:
        graphOnly = True
    else:
        graphOnly = False
    window = ApplicationWindow(graphOnly=graphOnly)

    try:
        window.view.show()
        #print("END:", time.time())
    except e:
        raise Exception("Error, something went wrong: " + e.msg)
    app.exec_()


