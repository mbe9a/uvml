import datetime as dt
from datetime import datetime
import time
import csv
import numpy as np
import matplotlib.pyplot as plt
from posixpath import os
import cPickle as pickle
import thread


### DO NOT directly call this method, it's just a helper method
def interrupt():
    raw_input('press enter to stop: ')
    thread.interrupt_main()

class TemperatureMonitor(object):

	def __init__(self, lakeshore, savedir='Temperature Logs'):
		self.savedir = savedir
		if not os.path.isdir(savedir):
			os.mkdir(savedir)
		self.lakeshore = lakeshore
		self.measurements = []
		self.measurement_num = 0
		self.date = dt.date.today()

	def measure(self, length, interval, name=None, prnt=True):
		today = self.date
		self.measurements.append({})
		if name:
			today = name
		with open(self.savedir + "/" + str(today) + "_TM.csv", "w") as csvfile:
			start = datetime.now()
			fieldnames = ['Time', 'Sensor 1 (K)', 'Sensor 2 (K)', 'Sensor 3 (K)', 'Sensor 4 (K)']
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
				writer.writerow({'Time': t.time(), 'Sensor 1 (K)': temp1, 'Sensor 2 (K)': temp2, 'Sensor 3 (K)': temp3, 'Sensor 4 (K)': temp4})
				self.measurements[self.measurement_num][t.time] = [temp1, temp2, temp3, temp4]
				if prnt:
					print "Time: " + t.time()
					print "Sensor 1: " + temp1
					print "Sensor 2: " + temp2
					print "Sensor 3: " + temp3
					print "Sensor 4: " + temp4
				time.sleep(interval)
		self.measurement_num += 1

		def save(self, name):
			pickle.dump(self, open(self.savedir + "/" + name + ".p", "wb"))

class DifferentialResistance(object):

	def __init__(self, lakeshore, keithley, savedir='Differential Resistance Measurements'):
		self.savedir = savedir
		if not os.path.isdir(savedir):
			os.mkdir(savedir)
		self.lakeshore = lakeshore
		self.keithley = keithley
		self.measurements = []
		self.measurement_num = 0
		self.date = dt.date.today()

	def measure(self, power_low_start=25, power_low_stop=100, power_low_step=25, power_high_start=125, power_high_stop=500, power_high_step=25, resistance=200, sleeptime=180, prnt=True):
		current_settings = range(power_low_start, power_low_stop + 1, power_low_step) + range(power_high_start, power_high_stop + 1, power_high_step)
		current_settings = np.sqrt(np.array(current_settings)/resistance)

		self.keithley.restore()
		self.keithley.source_mode("curr")
		self.keithley.source_fix("curr")
		self.keithley.measure_range("curr", "auto")
		self.keithley.set_amplitude("curr", 0)
		self.keithley.on = False
		self.keithley.measure_function(voltage=True, current=True)

		power = self.keithley.measure(power=True)
		temp1 = self.lakeshore.measure(1)
		temp2 = self.lakeshore.measure(2)
		temp3 = self.lakeshore.measure(3)
		temp4 = self.lakeshore.measure(4)

		with open(self.savedir + "/" + str(today) + "_DR.csv", "w") as csvfile:

			fieldnames = ['Power (W)', 'Sensor 1 (K)', 'Sensor 2 (K)', 'Sensor 3 (K)', 'Sensor 4 (K)', 'Time (s)']
			writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
			writer.writeheader()
			writer.writerow({'Power (W)': power, 'Sensor 1 (K)': temp1, 'Sensor 2 (K)': temp2, 'Sensor 3 (K)': temp3, 'Sensor 4 (K)': temp4, 'Time (s)': 0})
			start = datetime.now()

			for x in range(0, len(current_settings)):
				self.keithley.set_amplitude(current_settings[x]*0.001)
				power = self.keithley.measure(power=True)
				time.sleep(sleeptime)
				if x == 0:
					time.sleep(sleeptime)

				for y in range(0, 30):
					temp1 = self.lakeshore.measure(1)
					temp2 = self.lakeshore.measure(2)
					temp3 = self.lakeshore.measure(3)
					temp4 = self.lakeshore.measure(4)
					current = datetime.now()
					t = current - start
					writer.writerow({'Power (W)': power, 'Sensor 1 (K)': temp1, 'Sensor 2 (K)': temp2, 'Sensor 3 (K)': temp3, 'Sensor 4 (K)': temp4, 'Time (s)': t})
					self.measurements[self.measurement_num][t] = [temp1, temp2, temp3, temp4]

					if prnt:
						print "Time: " + t.time()
						print "Sensor 1: " + temp1
						print "Sensor 2: " + temp2
						print "Sensor 3: " + temp3
						print "Sensor 4: " + temp4
		self.measurement_num += 1

	def plot_DR(self):
		raise NotImplementedError

	def save(self, name):
			pickle.dump(self, open(self.savedir + "/" + name + ".p", "wb"))


