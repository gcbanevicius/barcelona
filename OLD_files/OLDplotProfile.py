#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, RadioButtons

MAX_PNTS = 1000

times = []
vals = []

with open('powerProfile.csv','r') as powerProfile:
    for line in powerProfile.readlines():
        line = line.split(',')
        times.append(line[0])
        vals.append(line[1])

fig, ax = plt.subplots()
plt.subplots_adjust(left=0.175, bottom=0.25)

l, = plt.plot(times[:MAX_PNTS], vals[:MAX_PNTS])

slideAx = plt.axes([0.175, 0.1, 0.75, 0.03])
slide = Slider(slideAx, 'Scroll Bar', 0, len(times) - MAX_PNTS)

def update(val):
    start = int(slide.val)
    end = start + MAX_PNTS
    #print start,end
    l.set_ydata(vals[start:end])
    fig.canvas.draw()
    #plt.plot(times[start:end], vals[start:end])

slide.on_changed(update)

plt.show()
