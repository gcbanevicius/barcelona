#!/usr/bin/env python

from __future__ import print_function

import re
import sys

def adjustTime(time, startTime):
    time = time - startTime
    return time

def print_helper(direction, depth, tup):
    tab = "  "
    #print(tab*depth + direction + " " + str(tup))
    print(tab*depth + str(tup))

def parseAbsoluteTimes(tuples, startTime=0, plotSpan=5000.0):
   
    DO_PRINT = False
    #DO_PRINT = True

    endTime = startTime+float(plotSpan)

    callStack = ["---"]
    methodTups = []
    lenTuples = len(tuples)
    # based on the assumption we start with an enter, which is reasonable...
    depth = -1
    for i in range(0, lenTuples):
        if tuples[i][2] > endTime:
            break

        currDirection = tuples[i][0]

        # if we are entering the function...
        if currDirection == "Enter":

            depth += 1
            currName = tuples[i][1]
            callStack.append(currName) 

            # check if last entry in log
            if i == (lenTuples - 1):
                currTime = tuples[i][2]
                #methodTup = (currName, float(currTime), float("+inf"), depth, currDirection)
                methodTup = (currName, float(currTime), float(endTime), depth, currDirection)
                methodTups.append(methodTup)
                if DO_PRINT: print_helper("Entr", depth, methodTup)
                continue
            else:
                currTime = tuples[i][2]
                if tuples[i+1][2] > endTime:
                    nextTime = endTime
                else:
                    nextTime = tuples[i+1][2] 
                nextTime = max(currTime, nextTime)
                methodTup = (currName, float(currTime), float(nextTime), depth, currDirection)
                methodTups.append(methodTup)
                if DO_PRINT: print_helper("Entr", depth, methodTup)

        # if we are exiting the function...
        elif currDirection == "Exit":
            if len(callStack) == 1:
                currName = callStack[-1]
                currTime = tuples[i][2]
                if  i == (lenTuples - 1):
                    nextTime = endTime
                elif tuples[i+1][2] > endTime:
                    nextTime = endTime
                else:
                    nextTime = tuples[i+1][2] 
                nextTime = max(currTime, nextTime)
                methodTup = (currName, float(currTime), float(nextTime), 0, "Enter") #currDirection)
                methodTups.append(methodTup)
                if DO_PRINT: print_helper("Exit", depth, methodTup)
                continue

            currName = callStack.pop()
            currName = callStack[-1]

            if  i == (lenTuples - 1):
                #methodTup = (currName, float(currTime), float("+inf"), depth, currDirection)
                methodTup = (currName, float(currTime), float(endTime), depth, currDirection)
                methodTups.append(methodTup)
                if DO_PRINT: print_helper("Exit", depth, methodTup)
                continue

            #else:
            currTime = tuples[i][2]
            if tuples[i+1][2] > endTime:
                nextTime = endTime
            else:
                nextTime = tuples[i+1][2] 

            if currTime == nextTime:
                depth -= 1
                continue

            nextTime = max(currTime, nextTime)
            methodTup = (currName, float(currTime), float(nextTime), depth, currDirection)
            methodTups.append(methodTup)
            if DO_PRINT: print_helper("Exit", depth, methodTup)

            depth -= 1

    return methodTups

def parseInputFile(inputFileName, startTime=0, plotSpan=5000):

    endTime = startTime+plotSpan

    clockStartTime = -1L
    finalLineTups = []
    with open(inputFileName, "r") as inputFile:
        lines = inputFile.readlines()
        lineTups = []
        for line in lines:
            line = line.strip()
            match = re.search('(Enter|Exit)\s+(\S+).*?(\d+$)', line)

            direction = match.group(1)
            name = match.group(2)
            time = long(match.group(3))

            if clockStartTime < 0:
                clockStartTime = time

            time = adjustTime(time, clockStartTime)

            logTuple = (direction, name, time)
            lineTups.append(logTuple)    

        for i in range(0, len(lineTups)):
            thisTup = lineTups[i]

            if i == len(lineTups)-1:
                if thisTup[2] < startTime:
                    time = startTime
                else:
                    time = thisTup[2]
                
                if time >= endTime:
                    break

                direction = thisTup[0]
                name = thisTup[1]
                logTuple = (direction, name, time)
                finalLineTups.append(logTuple)


            else:
                nextTup = lineTups[i+1]

                if thisTup[2] < startTime and nextTup[2] <= startTime:
                    continue
                elif thisTup[2] < startTime and nextTup[2] > startTime:
                    time = startTime
                else:
                    time = thisTup[2]
                
                if time >= endTime:
                    break 
 
                direction = thisTup[0]
                name = thisTup[1]
                logTuple = (direction, name, time)
                finalLineTups.append(logTuple)

    return finalLineTups

def main():

    startTime = -1L
    tuples = []

    if (len(sys.argv) > 1):
        fileName = sys.argv[1]
    else:
        fileName = "Logger.txt"

    with open(fileName, "r") as loggerFile:
        for line in loggerFile.readlines():
            line = line.strip()
            match = re.search('(Enter|Exit)\s+(\S+).*?(\d+$)', line)

            direction = match.group(1)
            name = match.group(2)
            time = long(match.group(3))

            if startTime < 0:
                startTime = time

            time = adjustTime(time, startTime)
 
            logTuple = (direction, name, time)
            tuples.append(logTuple)

    return parseAbsoluteTimes(tuples)

if __name__ == "__main__":
    main()
