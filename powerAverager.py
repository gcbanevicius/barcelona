#!/usr/bin/env python

import sys
import itertools

NUM=5000

def main():
    inputFileName = sys.argv[1]

    with open(inputFileName, 'r') as f:
        firstLine = f.readline()
        lines = []
        while "" not in lines:
            lines = [f.readline() for i in range(NUM)]
            if "" in lines: 
                break

            power = 0
            for i in range(0,len(lines)):
                line = lines[i]
                line = line.split(',')
                power += float(line[2])
            power /= NUM
            print power


if __name__ == "__main__":
    main()
