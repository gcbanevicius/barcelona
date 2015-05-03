#!/usr/bin/env python

from __future__ import print_function

import random
import re
import sys
import random

from PySide import QtGui, QtCore
import pyqtgraph as pg
import numpy as np

import generateCallgraph

PLOT_SPAN = (35 * 1000)

class ColorBlock:
    
    """Class with information about color-coded method rectangles"""

    def __init__(self, color, startTime, endTime):
        self.color = color
        self.startTime = startTime
        self.endTime = endTime
        print(self.startTime, self.endTime)
        
        if self.endTime != float('inf'):
            self.xVals = np.array(range(int(self.startTime),int(self.endTime)+1))
        else:
            self.xVals = np.array(range(int(self.startTime), int(self.startTime)+100))
        self.yVals = np.array([0.5]*len(self.xVals))

    def printFields(self):
        print(self.color, self.startTime, self.endTime)

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

    def __init__(self, methodName, startTime, endTime, depth, avgPower):
        self.methodName = methodName
        self.startTime = startTime
        self.endTime = endTime
        self.avgPower = avgPower
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

    def __init__(self, appWindow, methodTups, colorBlockList, colorMappings, startTime, *args, **kwargs):
        self.appWindow = appWindow
        self.methodTups = methodTups
        self.colorBlockList = colorBlockList
        self.colorMappings = colorMappings
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
        print("Before addMethodNames")
        self.addMethodNames(self.colorMappings)
        print("After addMethodNames")
       

    def addMethodNames(self, colorMappings):

        # get callstack and add buttons
        currDepth = 0
        currParent = None
        prevMethod = None
        parentList = []
        i = 0
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
                #endTime = methodTup[1] + random.randrange(100,500)
                endTime = methodTup[2]
                depth = methodTup[3]
                direction = methodTup[4]
                print("End time is:", endTime)

                methodInfo = MethodInfo(methodTup[0], methodTup[1], endTime, depth, randval)

                # time for fun stuff with hierarchy!... there are 3 cases
                if depth < currDepth:
                    currParent = parentList.pop() # there must be something on stack in this case
                    if currParent:
                        currParent.addChild(methodInfo)
                elif depth == currDepth:
                    if currParent:
                        currParent.addChild(methodInfo)
                elif depth > currDepth:
                    parentList.append(currParent)
                    currParent = prevMethod
                    currParent.addChild(methodInfo)
                # always do these two
                currDepth = depth
                prevMethod = methodInfo
                
                #if direction == "Enter":
                #    self.buttonHash[hashVal] = methodInfo
                self.buttonHash[hashVal] = methodInfo
            else:
                print("Argh... button was already in HashTable!", sys.stderr)
                sys.exit(1)

            # do not add buttons for the exit
            #if direction == "Exit":
            #    continue
            #print("At methodName %d, out of %d" % (i, len(self.methodTups)))
            #i += 1

            # add buttons to a list, to be referenced by eventFilter 
            # in the main ApplicationWindow class
            self.buttonList.append(button)

            # catch the last log that starts past end of time frame
            endTime = methodTup[1] - self.startTime
            #if methodTup[1] >= len(colorMappings):
            if endTime >= len(colorMappings):
                print(endTime, len(colorMappings))
                break

            # again, 5 mappings per millisec, so multiply
            #colorIdx = int(methodTup[1]) # * 5) # LOVE this stuff...
            colorIdx = int(endTime)
            #print(colorIdx, len(colorMappings))
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
            indentLabel = QtGui.QLabel(" ")
            indentLabel.setFixedSize(40*methodTup[3], 25)
            
            # create button
            containerButton = MyMethodButton(indentLabel, colorLabel, button)
            self.addLayout(containerButton)

    def buttonIterate(self):
        for button in self.buttonList:
            hashVal = hash(button)
            methodInfo = self.buttonHash[hashVal]
            methodInfo.printHelperCallgraph()


class MyPlot:

    """This is the class for the scrollable, zoomable plot"""


    def __init__(self, colorBlockList, colorMappings, startTime, *args, **kwargs):

        global PLOT_SPAN
        self.MAX_PNTS = 1000
        self.times = []
        self.vals = []
        endTime = startTime+PLOT_SPAN

        i = -1
        with open('powerProfile.csv','r') as powerProfile:
            for line in powerProfile.readlines()[(startTime*5):(endTime*5)+1]:
                i += 1
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
        global PLOT_SPAN
        self.graphOnly = graphOnly

        # read in info, generate and use callgraph
        if (len(sys.argv) > 1):
            fileName = sys.argv[1]
        else:
            fileName = "Logger.txt"

        # get the time range
        startTime = int(raw_input("Enter start time of the window (in seconds): "))*1000
        PLOT_SPAN = int(raw_input("Enter the size of the window (in seconds): "))*1000

        # popup window for hover on button
        self.popup = None

        # store the callgraph as tuples, one per method
        tuples = generateCallgraph.parseInputFile(fileName, startTime, PLOT_SPAN)
        self.methodTups = generateCallgraph.parseAbsoluteTimes(tuples, startTime, PLOT_SPAN)

        # create the color scheme
        if not self.graphOnly:
            self.colorBlockList = ColorBlockList()
            colors = ['red', 'green', 'blue', 'magenta', 'yellow', 'cyan']
            modVal = len(colors)
            i = 0
            for methodTup in self.methodTups:
                # no block for "empty" methods
                if not methodTup[1] == methodTup[2]:
                    if not methodTup[0] == "---":
                        color = colors[i]
                        i = (i+1) % modVal 
                    else:
                        color = 'lightGray'
                    colorBlock = ColorBlock(color, methodTup[1], methodTup[2])
                    self.colorBlockList.add(colorBlock)

            # a mapping of each time to a "color block"
            self.colorMappings = self.createColorMappings(self.colorBlockList, startTime)
        else:
            self.colorBlockList = ColorBlockList()
            self.colorMappings = []

        super(ApplicationWindow, self).__init__()

        ### Actual layout work begins ###
        pg.setConfigOption('background', 'w')
        self.view = pg.GraphicsView()
        gl = pg.GraphicsLayout()
        self.view.setCentralItem(gl)
        self.view.show()
        self.view.resize(1000, 600)

        ## Layout the method buttons 
        if not self.graphOnly:
            buttonVBox = MyMethodButtonPanel(self, self.methodTups, self.colorBlockList, self.colorMappings, startTime)
            #buttonVBox = QtGui.QVBoxLayout()
            #buttonVBox.buttonIterate()
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
        myPlot = MyPlot(self.colorBlockList, self.colorMappings, startTime)
        maxVal = float(myPlot.times[-1])
        self.mainPlot = pg.PlotWidget(name='MainPlot', title='Application Instantaneous Power')
        self.mainPlot.setMouseEnabled(y=False)
        self.mainPlot.setXRange(0, 250)
        self.mainPlot.plot(myPlot.x, myPlot.y, pen='b')
        #self.mainPlot.setLimits(xMin=0, xMax=maxVal)
        self.mainPlot.setLimits(xMin=startTime, xMax=startTime+PLOT_SPAN)
        self.mainPlot.setLabel('bottom', text="Time (msec)")
        self.mainPlot.setLabel('left', text="Power (mW)")
        proxyMainWidget = QtGui.QGraphicsProxyWidget()
        proxyMainWidget.setWidget(self.mainPlot)
        plotGl.addItem(proxyMainWidget)

        ## now do method rectangles
        if not self.graphOnly:
            plotGl.nextRow()
            colorRectPlot = pg.PlotWidget(name='ColorRectPlot')
            #colorRectPlot.hideAxis('left')
            colorRectPlot.hideAxis('bottom')
            colorRectPlot.hideButtons()
            colorRectPlot.setMouseEnabled(x=False, y=False)
            colorRectPlot.setXRange(0, 250)
            colorRectPlot.setXLink(self.mainPlot)
            #colorRectPlot.setLimits(xMin=0, xMax=maxVal, yMin=0, yMax=1)
            colorRectPlot.setLimits(xMin=startTime, xMax=startTime+PLOT_SPAN, yMin=0, yMax=1)
            colorRectPlot.setLabel('left', text=" ")

            print("Before drawMethodRects")
            #self.drawMethodRects(0, colorRectPlot, len(myPlot.vals), myPlot.MAX_PNTS)
            self.drawMethodRects(startTime, colorRectPlot, PLOT_SPAN, myPlot.MAX_PNTS)
            print("After drawMethodRects")

            proxyRectWidget = QtGui.QGraphicsProxyWidget()
            proxyRectWidget.setWidget(colorRectPlot)
            proxyRectWidget.setMaximumHeight(100)
            plotGl.addItem(proxyRectWidget)

    def createColorMappings(self, colorBlockList, startTime):

        global PLOT_SPAN

        colorMappings = []
        colorBlockListLength = colorBlockList.length()
        colorBlockIdx = 0
        colorBlock = colorBlockList.get(colorBlockIdx)
        colorBlockEndTime = colorBlock.endTime
        endTime = startTime+PLOT_SPAN

        i = -1
        print("now in createColorMappings", startTime, endTime)
        with open('powerProfile.csv','r') as powerProfile:
            for line in powerProfile.readlines()[(startTime*5):(endTime*5)+1]:
                i += 1
                if (i % 5) != 0:
                    continue
                #liney = line
                line = line.split(',')
                time = float(line[0])*1000.0 # convert to millisec
                #print(liney.rstrip(), "|||", line[0], "|||", time)

                if time > float(endTime):
                    break

                if time < colorBlockEndTime:
                    colorMappings.append(colorBlockIdx)
                else:
                    colorBlockIdx += 1
                    print("In createColorMappings:", time, colorBlockIdx, colorBlockList.length())
                    colorBlock = colorBlockList.get(colorBlockIdx)
                    colorBlockEndTime = colorBlock.endTime
                    colorMappings.append(colorBlockIdx)

        print("now leaving createColorMappings", len(colorMappings))
        return colorMappings

    def drawMethodRects(self, startVal, plotItem, valLen, maxPnts):
        #colorBlockIdx = self.colorMappings[startVal]
        colorBlockIdx = self.colorMappings[0]
        colorBlock = self.colorBlockList.get(colorBlockIdx)
        endPos = int(min(colorBlock.endTime, valLen))
        print(colorBlockIdx, self.colorBlockList.length())

        colorPen = pg.mkPen(colorBlock.color[0], width=10)
        print(colorBlock.printFields())
        plotItem.plot(colorBlock.xVals, colorBlock.yVals, pen=colorPen)

        while endPos < startVal+valLen:
            colorBlockIdx += 1
            colorBlock = self.colorBlockList.get(colorBlockIdx)
            colorPen = pg.mkPen(colorBlock.color[0], width=100)
            endPos = int(min(colorBlock.endTime, startVal+valLen))
            print(colorBlockIdx, self.colorBlockList.length())
            
            colorPen = pg.mkPen(colorBlock.color[0], width=10)
            colorBlock.printFields()
            plotItem.plot(colorBlock.xVals, colorBlock.yVals, pen=colorPen)
 
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
                avgPower = methodInfo.avgPower
                self.popup = MyPopup(startTime, endTime, avgPower)
                ### oooo baby, it's all here!
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
    except e:
        raise Exception("Oops, something went wrong: " + e.msg)
    app.exec_()


