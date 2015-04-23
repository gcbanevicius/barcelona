#!/usr/bin/env python

from __future__ import print_function

import sys
import re

def adjustTime(time, startTime):
    time = time - startTime
    return time


def print_helper(direction, depth, tup):
    tab = "  "
    print(tab*depth + direction + " " + str(tup))


def parseAbsoluteTimes(tuples):
   
    #DO_PRINT = False
    DO_PRINT = True

    callStack = []
    methodTups = []
    lenTuples = len(tuples)
    # based on the assumption we start with an enter, which is reasonable...
    depth = -1 # here we go, baby...
    for i in range(0, lenTuples):
        currDirection = tuples[i][0]

        # if we are entering the function...
        if currDirection == "Enter":

            depth += 1

            currName = tuples[i][1]
            callStack.append(currName) 

            # check if last entry in log
            if i == (lenTuples - 1):
                methodTup = (currName, float(currTime), float("+inf"), depth, currDirection)
                methodTups.append(methodTup)
                if DO_PRINT: print_helper("Entr", depth, methodTup)
                continue
            else:
                currTime = tuples[i][2]
                nextTime = tuples[i+1][2] 
                methodTup = (currName, float(currTime), float(nextTime), depth, currDirection)
                methodTups.append(methodTup)
                if DO_PRINT: print_helper("Entr", depth, methodTup)

        # if we are exiting the function...
        elif currDirection == "Exit":
 
            currName = callStack.pop()

            #if len(callStack) == 0:
            #    currName = "---"
            #else:                
            #    currName = callStack[-1]

            if  i == (lenTuples - 1):
                methodTup = (currName, float(currTime), float("+inf"), depth, currDirection)
                methodTups.append(methodTup)
                if DO_PRINT: print_helper("Exit", depth, methodTup)
                continue
            else:
                currTime = tuples[i][2]
                nextTime = tuples[i+1][2] 
                methodTup = (currName, float(currTime), float(nextTime), depth, currDirection)
                methodTups.append(methodTup)
                if DO_PRINT: print_helper("Exit", depth, methodTup)

            depth -= 1


    return methodTups

           
def parseRelativeTimes(tuples):

    callStack = []
    lenTuples = len(tuples)
    for i in range(0, lenTuples):
        currDirection = tuples[i][0]

        # if we are entering the function...
        if currDirection == "Enter":
            currName = tuples[i][1]
            callStack.append(currName) 

            # check if last entry in log
            if i == (lenTuples - 1):
                print("%s for ---" % (currName))
                continue
            else:
                currTime = tuples[i][2]
                nextTime = tuples[i+1][2] 
                print("%s for %d" % (currName, nextTime-currTime))
 

        # if we are exiting the function...
        elif currDirection == "Exit":
            callStack.pop()

            if len(callStack) == 0:
                currName = "---"
            else:                
                currName = callStack[-1]

            if  i == (lenTuples - 1):
                print("%s for ---" % (currName))
                continue
            else:
                currTime = tuples[i][2]
                nextTime = tuples[i+1][2] 
                print("%s for %d" % (currName, nextTime-currTime))
            

def parseInputFile(inputFileName):

    startTime = -1L
    tuples = []
    with open(inputFileName, "r") as inputFile:
        for line in inputFile.readlines():
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

    return tuples   


def main():

    startTime = -1L
    tuples = []

    if (len(sys.argv) > 1):
        fileName = sys.argv[1]
    else:
        fileName = "Logger.txt"

    with open(fileName, "r") as loggerFile:
        for line in loggerFile.readlines():
            #print(line)
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
            #print(logTuple)

    return parseAbsoluteTimes(tuples)
    #parseRelativeTimes(tuples)


if __name__ == "__main__":
    main()
