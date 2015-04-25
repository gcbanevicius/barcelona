#!/usr/bin/env python

from __future__ import print_function

import random
import re
import sys
import random

from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg

import numpy as np

import generateCallgraph


class ColorBlock:
    
    """Class with information about color-coded method rectangles"""

    def __init__(self, color, startTime, endTime):
        self.color = color
        self.startTime = startTime
        self.endTime = endTime

    def printFields(self):
        print(self.color, self.startTime, self.endTime)

    def printFieldsVerbose(self):
        print("Color is:", self.color, " | Start time:",  self.startTime, " | End time:", self.endTime)

    def is_empty(self):
        if self.startTime == self.endTime:
            return True
        else:
             return False

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

    """Wraps relevant info about a method"""

    def __init__(self, methodName, startTime, endTime, avgPower):
        self.methodName = methodName
        self.startTime = startTime
        self.endTime = endTime
        self.avgPower = avgPower

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

    def __init__(self, appWindow, methodTups, colorBlockList, colorMappings, *args, **kwargs):
        self.appWindow = appWindow
        self.methodTups = methodTups
        self.colorBlockList = colorBlockList
        self.colorMappings = colorMappings
        self.buttonList = []

        self.colorHash = {
            'red': QtCore.Qt.red,
            'green': QtCore.Qt.green,
            'blue': QtCore.Qt.blue,
            'yellow': QtCore.Qt.yellow,
        }

        super(MyMethodButtonPanel, self).__init__(*args, **kwargs)
        
        # this is a mapping of method-name-buttons to relevant info
        self.buttonHash = {}
        self.addMethodNames(self.colorMappings)
       

    def addMethodNames(self, colorMappings):

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

            # add buttons to a list, to be referenced by eventFilter 
            # in the main ApplicationWindow class
            self.buttonList.append(button)

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

            containerButton = MyMethodButton(indentLabel, colorLabel, button)
            self.addLayout(containerButton)


class MyPlot:

    """This is the class for the scrollable, zoomable plot"""


    def __init__(self, colorBlockList, colorMappings, *args, **kwargs):
        self.MAX_PNTS = 1000
        self.times = []
        self.vals = []
        # don't need the below as of now...
        self.methNames =[]
        self.colorBlockList = colorBlockList
        self.colorMappings = colorMappings

        with open('powerProfile.csv','r') as powerProfile:
            for line in powerProfile.readlines():
                line = line.split(',')
                self.times.append(line[0])
                #self.times.append(float(line[0]) * 1000)
                self.vals.append(line[1])
                self.methNames.append(line[2])

        # get data for plotting
        self.x = np.array(self.times, dtype='float_')
        self.y = np.array(self.vals, dtype='float_')
        #plotItem.plot(x, y, pen='b')


    def drawMethodRects(self, startVal):
        colorBlockIdx = self.colorMappings[startVal]
        colorBlock = self.colorBlockList.get(colorBlockIdx)

        colorBlock.printFields()
        
        # times are in msec, so divide by 1000 to get seconds
        startPos = colorBlock.startTime/1000
        endPos = min(colorBlock.endTime/1000, len(self.vals))
        self.axes.axvspan(startPos, endPos, ymin=0, ymax=0.05, \
                          facecolor=colorBlock.color, alpha=0.5)

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

        # popup window for hover on button
        self.popup = None

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
        mod = len(colors)
        i = 0
        for methodTup in self.methodTups:
            print(methodTup)
            colorBlock = ColorBlock(colors[i], methodTup[1], methodTup[2])
            if not colorBlock.is_empty():
                colorBlock.printFields()
                self.colorBlockList.add(colorBlock)
                i = (i+1) % mod 

        self.colorMappings = self.createColorMappings(self.colorBlockList)


        ### Actual layout work begins ###
        pg.setConfigOption('background', 'w')
        self.view = pg.GraphicsView()
        gl = pg.GraphicsLayout()
        self.view.setCentralItem(gl)
        self.view.show()
        # resize it
        #self.view.resize(800, 600)

        ## Layout the method buttons 
        #gl.nextRow()
        buttonVBox = MyMethodButtonPanel(self, self.methodTups, self.colorBlockList, self.colorMappings)
        scrollWidget = QtGui.QWidget()
        scrollWidget.setLayout(buttonVBox)

        self.buttonHash = buttonVBox.buttonHash
        for b in buttonVBox.buttonList:
            b.installEventFilter(self)

        scrollArea = QtGui.QScrollArea()
        scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scrollArea.setWidgetResizable(False)
        scrollArea.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Expanding)
        scrollArea.setWidget(scrollWidget)

        proxyScrollWidget = QtGui.QGraphicsProxyWidget()
        proxyScrollWidget.setWidget(scrollArea)
        gl.addItem(proxyScrollWidget)

        ## Layout the actual plot
        plotGl = gl.addLayout()
        
        # start with plot
        myPlot = MyPlot(self.colorBlockList, self.colorMappings)
        maxVal = float(myPlot.vals[-1])

        #self.mainPlot = plotGl.addPlot(name='MainPlot', title='MainPlot')
        self.mainPlot = pg.PlotWidget(name='MainPlot', title='MainPlot')
        self.mainPlot.setMouseEnabled(y=False)
        self.mainPlot.setXRange(0.00, 0.05)
        self.mainPlot.plot(myPlot.x, myPlot.y, pen='b')
        #self.mainPlot.setLimits(xMin=0, xMax=maxVal/5000)
        self.mainPlot.setLimits(xMin=0)

        proxyMainWidget = QtGui.QGraphicsProxyWidget()
        proxyMainWidget.setWidget(self.mainPlot)
        plotGl.addItem(proxyMainWidget)


        ## now do method rectangles
        plotGl.nextRow()

        #colorRectPlot = plotGl.addPlot(name='ColorRectPlot', title='ColorRectPlot')
        colorRectPlot = pg.PlotWidget(name='ColorRectPlot', title='ColorRectPlot')
        #colorRectPlot.hideAxis('left')
        #colorRectPlot.hideAxis('bottom')
        colorRectPlot.hideButtons()
        
        colorRectPen = pg.mkPen('y', width=500)
        newY = [2000] * len(myPlot.y)
        newY = np.array(newY, dtype='float_')
        colorRectPlot.plot(myPlot.x, newY, pen=colorRectPen)
        #colorRectPlot.plot(myPlot.x, myPlot.y, pen='r')

        colorRectPlot.setMouseEnabled(x=False, y=False)
        colorRectPlot.setXRange(0.00, 0.05)
        colorRectPlot.setXLink(self.mainPlot)
        #colorRectPlot.setLimits(xMin=0, xMax=maxVal/5000) # argh the conversions!!!
        colorRectPlot.setLimits(xMin=0)

        self.drawMethodRects(0, colorRectPlot, len(myPlot.vals), myPlot.MAX_PNTS)

        proxyRectWidget = QtGui.QGraphicsProxyWidget()
        proxyRectWidget.setWidget(colorRectPlot)
        proxyRectWidget.setMaximumHeight(100)
        plotGl.addItem(proxyRectWidget)

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

    def drawMethodRects(self, startVal, plotItem, valLen, maxPnts):
        print("Entering drawMethodRects!!!")

        #scale = 0.2
        #scale = 5
        scale = 0.001

        colorBlockIdx = self.colorMappings[startVal]
        colorBlock = self.colorBlockList.get(colorBlockIdx)

        colorBlock.printFieldsVerbose()
        
        # times are in msec, so divide by 1000 to get seconds
        startPos = int(colorBlock.startTime * scale)
        endPos = int(min(colorBlock.endTime * scale, valLen))
        print("HERE WE BE", startPos, endPos)
        #self.axes.axvspan(startPos, endPos, ymin=0, ymax=0.05, \
        #                  facecolor=colorBlock.color, alpha=0.5)
        xVals = np.array(range(startPos,endPos), dtype='float_')
        yVals = np.array([2000]*len(xVals), dtype='float_')
        colorPen = pg.mkPen(colorBlock.color[0], width=100)
        plotItem.plot(xVals, yVals, pen=colorPen)

        maxPos = startPos + maxPnts
        while endPos < maxPos:
            colorBlockIdx += 1
            colorBlock = self.colorBlockList.get(colorBlockIdx)
            colorBlock.printFieldsVerbose()
            colorPen = pg.mkPen(colorBlock.color[0], width=100)
            startPos = int(colorBlock.startTime * scale)
            endPos = int(min(colorBlock.endTime * scale, valLen))

            xVals = np.array(range(startPos,endPos), dtype='float_')
            yVals = np.array([2000]*len(xVals), dtype='float_')
            colorPen = pg.mkPen(colorBlock.color[0], width=100)
            plotItem.plot(xVals, yVals, pen=colorPen)

            #print(endPos, "!!!")
            #self.axes.axvspan(colorBlock.startTime * scale, endPos, ymin=0, ymax=0.05, \
            #                  facecolor=colorBlock.color, alpha=0.5)

        print("Exiting drawMethodRects!!!")
 

    def eventFilter(self, object, event):

        if event.type() == QtCore.QEvent.MouseButtonPress:
            hashVal = hash(object) # the object is the button
            startTime = self.buttonHash[hashVal].startTime #[0]
            #position = startTime * 5 # time is recorded in fifths of a millisecond
            #self.slider.setValue(position)
            position = startTime / 1000
            self.mainPlot.setXRange(position, position + 0.25)
            

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

