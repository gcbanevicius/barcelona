#!/usr/bin/env python

from __future__ import print_function

import sys
import re

def adjustTime(time, startTime):
   # get rid of decimal to avoid weird float precision issues
    time = time * 10
    startTime = startTime * 10
    time = time - startTime
    time = time/10
    return time


def getMethodTuples(methodInputFileName):

    startTime = -1L
    
    tuples = []
    with open(methodInputFileName, "r") as loggerFile:
        for line in loggerFile.readlines():
            line = line.strip()
            match = re.search('(Enter|Exit)\s(\S+).*?(\d+$)', line)

            direction = match.group(1)
            name = match.group(2)
            time = long(match.group(3))

            # found starting time
            if startTime < 0:
                startTime = time

            time = adjustTime(time, startTime)
            logTuple = (direction, name, time)
            tuples.append(logTuple)

    callStack = []
    methodTuples = []
    lenTuples = len(tuples)
    for i in range(0, lenTuples):
        currDirection = tuples[i][0]

        # if we are entering the function...
        if currDirection == "Enter":
            currName = tuples[i][1]
            callStack.append(currName) 

            # check if last entry in log
            if i == (lenTuples - 1):
                #print("%s for ---" % (currName))
                methodTup = (float(currTime), currName)
                methodTuples.append(methodTup)
                #print(methodTup)               
                continue
            else:
                currTime = tuples[i][2]
                #nextTime = tuples[i+1][2] 
                #print("%s for %d" % (currName, nextTime-currTime))
                #print("%s for %d" % (currName, currTime))
                methodTup = (float(currTime), currName)
                methodTuples.append(methodTup)
                #print(methodTup)


        # if we are exiting the function...
        elif currDirection == "Exit":
            callStack.pop()

            if len(callStack) == 0:
                currName = "---"
            else:                
                currName = callStack[-1]

            if  i == (lenTuples - 1):
                #print("%s for ---" % (currName))
                methodTup = (float(currTime), currName)
                methodTuples.append(methodTup)
                #print(methodTup)
                continue
            else:
                currTime = tuples[i][2]
                #nextTime = tuples[i+1][2] 
                #print("%s for %d" % (currName, nextTime-currTime))
                #print("%s for %d" % (currName, currTime))
                methodTup = (float(currTime), currName)
                methodTuples.append(methodTup)
                #print(methodTup)

    return methodTuples


def getPowerTuples(powerInputFileName):
    
    powerTuples = []
    startTime = -1L
    with open(powerInputFileName, "r") as loggerFile:
        for line in loggerFile.readlines()[1:]:
            line = line.strip()
            line = line.split(',')

            time = float(line[0])
            avgPower = float(line[2])

            if startTime < 0:
                startTime = time

            time = adjustTime(time, startTime)
 
            logTuple = (time, avgPower)
            powerTuples.append(logTuple)
            #print(logTuple)
            
    return powerTuples

# remove methods with 0ms durations
def dedupMethodTuples(methodTuples):
    newMethodTuples = []
    for i in range(0, len(methodTuples)-1):
        if methodTuples[i][0] != methodTuples[i+1][0]:
            newMethodTuples.append(methodTuples[i])

    newMethodTuples.append(methodTuples[-1])
    return newMethodTuples
 
def combineMethodsWithPower(methodTuples, powerTuples):

    # we know that len(power) > len(methods),
    # since power is every 0.2ms, but
    # methods is at MOST every ms

    mi = 0 
    ml = len(methodTuples)
    currName = methodTuples[mi][1]
    if mi == ml:
        nextTime = float("+inf") 
    else:
        nextTime = methodTuples[mi+1][0]

    for pi in range(0, len(powerTuples)):
        if currName == '---':
            break

        currPowerTuple = powerTuples[pi]
        currTime = currPowerTuple[0]
        currAvgPower = currPowerTuple[1]

        if currTime < nextTime:
            print("%.4f,%.3f,%s" %(currTime, currAvgPower, currName))

        else:
            mi = mi+1
            currName = methodTuples[mi][1]
            if mi == ml:
                nextTime = float("+inf")
            else:
                nextTime = methodTuples[mi+1][0]

            # we don't want to print out null method, but we break at top of loop
            if currName != '---':
                print("%.4f,%.3f,%s" %(currTime, currAvgPower, currName))

    return 0


def main():
    if len(sys.argv) < 3:
        print("Error, need 2 input files: [methodTrace] [powerTrace]", file=sys.stderr)
        sys.exit(1)

    methodInputFileName = sys.argv[1]
    powerInputFileName = sys.argv[2]

    methodTuples = getMethodTuples(methodInputFileName)
    methodTuples = dedupMethodTuples(methodTuples)
    #print(methodTuples)
    powerTuples = getPowerTuples(powerInputFileName)
    combineMethodsWithPower(methodTuples, powerTuples)


if __name__ == "__main__":
    main()
