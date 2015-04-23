#!/usr/bin/env python

from __future__ import print_function

import sys
import re

def adjustTime(time, startTime):
    #time = float(time - startTime)
    # time = time / 1000 # ms => sec
    # return time
    
    # get rid of decimal to avoid weird float precision issues
    time = time * 10
    startTime = startTime * 10
    
    #print(time, startTime)

    time = time - startTime
    time = time/10

    return time

def main():
    
    inputFileName = sys.argv[1]
    startTime = -1L

    tuples = []
    with open(inputFileName, "r") as loggerFile:
        for line in loggerFile.readlines()[1:]:
            line = line.strip()
            #match = re.search('(Enter|Exit)\s(\S+).*?(\d+$)', line)
            line = line.split(',')

            #direction = match.group(1)
            #name = match.group(2)
            #time = long(match.group(3))
            time = float(line[0])
            avgPower = float(line[2])

            if startTime < 0:
                startTime = time

            time = adjustTime(time, startTime)
 
            logTuple = (time, avgPower)
            tuples.append(logTuple)
            print(logTuple)

           
#    callStack = []
#    lenTuples = len(tuples)
#    for i in range(0, lenTuples):
#        currDirection = tuples[i][0]
#
#        # if we are entering the function...
#        if currDirection == "Enter":
#            currName = tuples[i][1]
#            callStack.append(currName) 
#
#            # check if last entry in log
#            if i == (lenTuples - 1):
#                print("%s for ---" % (currName))
#                continue
#            else:
#                currTime = tuples[i][2]
#                nextTime = tuples[i+1][2] 
#                print("%s for %d" % (currName, nextTime-currTime))
# 
#
#        # if we are exiting the function...
#        elif currDirection == "Exit":
#            callStack.pop()
#
#            if len(callStack) == 0:
#                currName = "---"
#            else:                
#                currName = callStack[-1]
#
#            if  i == (lenTuples - 1):
#                print("%s for ---" % (currName))
#                continue
#            else:
#                currTime = tuples[i][2]
#                nextTime = tuples[i+1][2] 
#                print("%s for %d" % (currName, nextTime-currTime))
            
       


if __name__ == "__main__":
    main()
