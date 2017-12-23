"""
Mike Eller
UVML
November 2017
"""

import datetime as dt
from datetime import datetime
import time
import csv
import numpy as np
import matplotlib.pyplot as plt
import os
import cPickle as pickle
import thread

plt.style.use('bmh')


# DO NOT directly call this method, it's just a helper method
def interrupt():
    raw_input('press enter to stop: ')
    thread.interrupt_main()


class TemperatureMonitor(object):

	def __init__(self, lakeshore, savedir='Temperature Logs'):
		self.savedir = savedir
		if not os.path.isdir(savedir):
			os.mkdir(savedir)
		self.lakeshore = lakeshore
		self.measurements = {}
		self.date = dt.date.today()

	def measure(self, length, interval, name=None, prnt=True):
		today = self.date
		if name:
			today = name
		with open(self.savedir + "/" + str(today) + "_TM.csv", "w") as csvfile:
			start = datetime.now()
			fieldnames = ['Time', 'Sensor 1 (K)', 'Sensor 2 (K)', 'Sensor 3 (K)', 'Sensor 4 (K)']
			writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
			writer.writeheader()
			try:
				thread.start_new_thread(interrupt, ())
				while 1:
					t = datetime.now()
					current = t - start
					if current.total_seconds() > length:
						break
					temp1 = self.lakeshore.measure(1)
					temp2 = self.lakeshore.measure(2)
					temp3 = self.lakeshore.measure(3)
					temp4 = self.lakeshore.measure(4)
					writer.writerow({'Time': t.time(), 'Sensor 1 (K)': temp1, 'Sensor 2 (K)': temp2, 'Sensor 3 (K)': temp3,
					                 'Sensor 4 (K)': temp4})
					self.measurements[name] = {'temp1': temp1, 'temp2': temp2, 'temp3': temp3, 'temp4': temp4, 'time': t}
					if prnt:
						print "Time: " + str(t.time())
						print "Sensor 1: " + temp1
						print "Sensor 2: " + temp2
						print "Sensor 3: " + temp3
						print "Sensor 4: " + temp4
					time.sleep(interval)

			except KeyboardInterrupt:
				pass

	def save(self, name):
		pickle.dump(self, open(self.savedir + "/" + name + ".p", "wb"))


class Measurement(dict):
	def __init__(self, *arg, **kw):
		super(Measurement, self).__init__(*arg, **kw)
		try:
			self.name = kw['name']
		except KeyError:
			return


class DifferentialResistance(object):

	def __init__(self, lakeshore, keithley, savedir='Differential Resistance Measurements'):
		self.savedir = savedir
		if not os.path.isdir(savedir):
			os.mkdir(savedir)
		self.lakeshore = lakeshore
		self.keithley = keithley
		self.measurements = {}
		self.date = dt.date.today()

	def measure(self, name, power_low_start=25, power_low_stop=100, power_low_step=25, power_high_start=125,
	            power_high_stop=500, power_high_step=25, resistance=200, sleeptime=180, prnt=True):
		current_settings = range(power_low_start, power_low_stop + 1, power_low_step) \
		                   + range(power_high_start, power_high_stop + 1, power_high_step)
		current_settings = np.sqrt(np.array(current_settings)/resistance)

		self.keithley.restore()
		self.keithley.source_mode("curr")
		self.keithley.source_fix("curr")
		self.keithley.source_range("curr", "auto")
		self.keithley.set_amplitude("curr", 0)
		self.keithley.on = False
		self.keithley.measure_function(voltage=True, current=True)
		self.measurements[name] = []

		power = self.keithley.measure(power=True)
		temp1 = self.lakeshore.measure(1)
		temp2 = self.lakeshore.measure(2)
		temp3 = self.lakeshore.measure(3)
		temp4 = self.lakeshore.measure(4)

		with open(self.savedir + "/" + str(self.date) + "_DR.csv", "w") as csvfile:

			fieldnames = ['Power (W)', 'Sensor 1 (K)', 'Sensor 2 (K)', 'Sensor 3 (K)', 'Sensor 4 (K)', 'Time (s)']
			writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
			writer.writeheader()
			writer.writerow({'Power (W)': power, 'Sensor 1 (K)': temp1, 'Sensor 2 (K)': temp2, 'Sensor 3 (K)': temp3,
			                 'Sensor 4 (K)': temp4, 'Time (s)': 0})
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
					writer.writerow({'Power (W)': power, 'Sensor 1 (K)': temp1, 'Sensor 2 (K)': temp2,
					                 'Sensor 3 (K)': temp3, 'Sensor 4 (K)': temp4, 'Time (s)': t})

					m = Measurement({'power': power, 'temp1': temp1, 'temp2': temp2,
					                   'temp3': temp3, 'temp4': temp4, 'time': t})
					self.measurements[name].append(m)

					if prnt:
						print "Time: " + str(t)
						print "Sensor 1: " + temp1
						print "Sensor 2: " + temp2
						print "Sensor 3: " + temp3
						print "Sensor 4: " + temp4

	def plot_dr(self, name):
		power = []
		temp1 = []
		temp2 = []
		temp3 = []
		temp4 = []

		for m in range(0, len(self.measurements[name])):
			power.append(float(self.measurements[name][m]['power']))
			temp1.append(float(self.measurements[name][m]['temp1']))
			temp2.append(float(self.measurements[name][m]['temp2']))
			temp3.append(float(self.measurements[name][m]['temp3']))
			temp4.append(float(self.measurements[name][m]['temp4']))

		temp21 = []
		temp32 = []
		temp43 = []
		temp41 = []
		thot = []
		s = []
		for p in range(0, len(power) - 1):
			t21 = (((temp2[p + 1] - temp1[p + 1])(temp2[p] - temp1[p]))/(power[p + 1] - power[p]))
			t32 = (((temp3[p + 1] - temp2[p + 1])(temp3[p] - temp2[p])) / (power[p + 1] - power[p]))
			t43 = (((temp4[p + 1] - temp3[p + 1])(temp4[p] - temp3[p])) / (power[p + 1] - power[p]))
			t41 = (((temp4[p + 1] - temp1[p + 1])(temp4[p] - temp1[p])) / (power[p + 1] - power[p]))
			temp21.append(t21)
			temp32.append(t32)
			temp43.append(t43)
			temp41.append(t41)
			thot.append(temp4[p + 1])
			s.append(t21 + t32 + t43)

		fig = plt.figure(figsize=(11, 7))

		plt.plot(thot, temp21, '^--', label='Sensor 2 to 1')
		plt.plot(thot, temp32, 'o--', label='Sensor 3 to 2')
		plt.plot(thot, temp43, '*--', label='Sensor 4 to 3')
		plt.plot(thot, temp41, 's--', label='Sensor 4 to 1')
		plt.plot(thot, s, 'o--', label='Sum')

		plt.title('Differential Thermal Resistance')
		plt.xlabel(r'$T_{Hot}$ (K)')
		plt.ylabel(r'Thermal Resistance $\frac{K}{W}$')

		plt.legend()
		plt.show()

		return fig

	def save(self, name):
			pickle.dump(self, open(self.savedir + "/" + name + ".p", "wb"))


class Tc(object):

	def __init__(self, lakeshore, keithley, savedir='Tc Measurements'):
		self.savedir = savedir
		if not os.path.isdir(savedir):
			os.mkdir(savedir)
		self.lakeshore = lakeshore
		self.k = keithley
		self.measurements = {}
		self.date = dt.date.today()

	def measure(self, name, liveplot=True):
		# self.k.restore()
		# self.k.measure_function(voltage=True)
		# self.k.set_channel(1)
		# self.k.set_channel_range(1, 1)
		# self.k.set_power_line_cycles(1)
		#
		# v = []
		# temp = []
		# try:
		# 	thread.start_new_thread(interrupt, ())
		# 	self.k.set_channel(1)
		# 	self.k.on = True
		# 	while 1:
		# 		v.append(float(self.k.measure()))
		# 		temp.append(self.lakeshore.mesure())
		# 		plt.cla()
		# 		plt.clf()
		# 		plt.plot(temp, v)
		# 		plt.pause(0.01)
		# except KeyboardInterrupt:
		# 	pass
		#
		# with open(self.savedir + '/' + name + '.csv', 'w') as csvfile:
		# 	fieldnames = ['V', 'Temp (K)']
		# 	writer = csv.DictWriter(csvfile, fieldname=fieldnames)
		# 	writer.writeheader()
		# 	for x in range(0, len(v)):
		# 		writer.writerow({'V': v[x], 'Temp (K)': temp[x]})
		#
		# fig = plt.figure()
		# plt.plot(temp, v)
		# fig.savefig(self.savedir + '/' + name + '.png')
		raise NotImplementedError

	def save(self, name):
			pickle.dump(self, open(self.savedir + "/" + name + ".p", "wb"))
