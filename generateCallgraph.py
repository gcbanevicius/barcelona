#!/usr/bin/env python

from __future__ import print_function

import sys
import re

def adjustTime(time, startTime):
    time = time - startTime
    return time


def parseAbsoluteTimes(tuples):

    callStack = []
    methodTups = []
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
                methodTups.append(methodTup)
                print(methodTup)               
                continue
            else:
                currTime = tuples[i][2]
                #nextTime = tuples[i+1][2] 
                #print("%s for %d" % (currName, nextTime-currTime))
                #print("%s for %d" % (currName, currTime))
                methodTup = (float(currTime), currName)
                methodTups.append(methodTup)
                print(methodTup)

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
                methodTups.append(methodTup)
                print(methodTup)
                continue
            else:
                currTime = tuples[i][2]
                #nextTime = tuples[i+1][2] 
                #print("%s for %d" % (currName, nextTime-currTime))
                #print("%s for %d" % (currName, currTime))
                methodTup = (float(currTime), currName)
                methodTups.append(methodTup)
                print(methodTup)

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
            

def main():

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

            time = adjustTime(time, startTime)
 
            logTuple = (direction, name, time)
            tuples.append(logTuple)
            #print(logTuple)

    return parseAbsoluteTimes(tuples)
    #parseRelativeTimes(tuples)


if __name__ == "__main__":
    main()
