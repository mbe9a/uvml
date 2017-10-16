import datetime as dt
from datetime import datetime
import time
import csv
import numpy as np
import matplotlib.pyplot as plt
import os

class Monitor(object):

	def __init__(self, lakeshore, savedir='Temperature Logs'):
		self.savedir = savedir
		if not os.path.isdir(savedir):
			os.mkdir(savedir)
		self.lakeshore = lakeshore

	def measure(self, length, interval, name=None, prnt=True):
		today = dt.date.today()
		if name:
			today = name
		with open(self.savedir + "/" + str(today) + ".csv", "w") as csvfile:
			start = datetime.now()
			fieldnames = ['Time', 'Sensor 1', 'Sensor 2', 'Sensor 3', 'Sensor 4']
			writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
			writer.writeheader()
			while(1):
				t = datetime.now()
				current = t - start
				if current.total_seconds() > length:
					break
				temp1 = self.lakeshore.measure(1)
				
				temp2 = self.lakeshore.measure(2)
				
				temp3 = self.lakeshore.measure(3)
				
				temp4 = self.lakeshore.measure(4)
				writer.writerow({'Time': t.time(), 'Sensor 1': temp1, 'Sensor 2': temp2, 'Sensor 3': temp3, 'Sensor 4': temp4})
				if prnt:
					print "Time: " + t.time()
					print "Sensor 1: " + temp1
					print "Sensor 2: " + temp2
					print "Sensor 3: " + temp3
					print "Sensor 4: " + temp4
				time.sleep(interval)
