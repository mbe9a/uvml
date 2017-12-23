"""
Mike Eller
UVML
November 2017
"""

from template_instrument import LANINST
import numpy as np
import csv


class Keithley(LANINST):
	def __init__(self, addr, **kwargs):
		LANINST.__init__(self, addr, **kwargs)
		self._on = False
		self.id()

	@property
	def on(self):
		return self._on

	@on.setter
	def on(self, value):
		self._on = bool(value)
		if self._on:
			self.write(":outp:stat 1")
		else:
			self.write(":outp:stat 0")

	def restore(self):
		self.write("*RST")

	def source_mode(self, mode):
		self.write(":SOUR:FUNC:MODE " + mode)

	def source_fix(self, mode):
		self.write(":SOUR:" + mode + ":mode fix")

	def measure_range(self, mode, rng):
		self.write(":SOUR:" + mode + ":rang:" + rng + " on")

	def set_amplitude(self, mode, amp):
		self.write(":SOUR:" + mode + ":lev:imm:ampl " + str(amp))

	def measure_function(self, voltage=False, current=False):
		if voltage and current:
			self.write(":SENS:FUNC  'VOLT', 'CURR'")
		elif voltage:
			self.write(":SENS:FUNC  'VOLT'")
		elif current:
			self.write(":SENS:FUNC  'CURR'")

	def measure(self, power=False):
		if self.on:
			if power:
				s = self.ask("read?")
				return float(s[0:13])*float(s[14:27])
			return self.ask("read?")
		else:
			return "Not permitted with output off."


class Lakeshore(LANINST):

	def __init__(self, addr, **kwargs):
		LANINST.__init__(self, addr, **kwargs)

	def measure(self, sensor):
		return np.float(self.ask("KRDG? " + str(sensor)))


display_combos = {'A1B1': 'L - D', 'A1B2': 'L - Q', 'A1B3': 'L - ESR/G', 'A2B1': 'C - D', 'A2B2': 'C - Q',
                  'A2B3': 'C - ESR/G', 'A3B1': 'R - X/B', 'A3B2': 'R - L/C', 'A3B3': 'R - X/B',
                  'A4B1': '|Z| - ' + unichr(0x3b8).encode('utf-8'),
                  'A4B2': '|Z| - ' + unichr(0x3b8).encode('utf-8'),
                  'A4B3': '|Z| - ' + unichr(0x3b8).encode('utf-8')}

circuit_mode = {'C1': 'AUTO', 'C2': 'SERIES', 'C3': 'PARALLEL'}

deviation_measurement = {'D0': 'OFF', 'D1': unichr(0x394).encode('utf-8'), 'D2': unichr(0x394).encode('utf-8') + '%'}

frequency_step = {'F11': '10 kHz', 'F12': '20 (30) kHz', 'F13': '40 (50) kHz', 'F14': '100 kHz',
                  'F15': '200 (300) kHz', 'F16': '400 (500) kHz', 'F17': '1 MHz', 'F18': '2 (3) MHz',
                  'F19': '4 (5) MHz', 'F20': '10 MHz', 'F21': '*1', 'F22': '*2'}

high_resolution = {'H0': 'OFF', 'H1': 'ON'}

data_ready = {'I0': 'OFF', 'I1': 'ON'}

multiplier = {'M1': 'X0.01', 'M2': 'X0.1', 'M3': 'X1'}

lcrz_range = {'R31': 'AUTO', 'R32': 'MANUAL', 'R11': '1000 fF / 100 nH',
              'R12': '10 pF / 1000 nH / 100 m' + unichr(0x3a9).encode('utf-8'),
              'R13': '100 pF / 10 ' + unichr(0x3bc).encode('utf-8') + 'H / 10 ' + unichr(0x3a9).encode('utf-8'),
              'R14': '1000 pF / 100 ' + unichr(0x3bc).encode('utf-8') + 'H / 100 ' + unichr(0x3a9).encode('utf-8'),
              'R15': '10 nF / 100 ' + unichr(0x3bc).encode('utf-8') + 'H / 10 k' + unichr(0x3a9).encode('utf-8'),
              'R16': '100 nF / 1 mH / 100 k' + unichr(0x3a9).encode('utf-8'),
              'R17': '1000 nF / 10 mH / 10 k' + unichr(0x3a9).encode('utf-8'),
              'R18': '10 ' + unichr(0x3bc).encode('utf-8') + 'F / 1000 mH / 1000 k' + unichr(0x3a9).encode('utf-8'),
              'R19': '100 ' + unichr(0x3bc).encode('utf-8') + 'F / 10H / 10 M' + unichr(0x3a9).encode('utf-8'),
              'R20': '100 H'}

self_test = {'S0': 'OFF', 'S1': 'ON'}

trigger = {'T1': 'INT', 'T2': 'EXT', 'T3': 'HOLD / MANUAL'}

zero = {'Z0': 'OPEN', 'ZS': 'SHORT'}

sweep_kHz = [10, 20, 40, 100, 200, 400]

sweep_MHz = [1, 2, 4, 10]


class LCRMeter(LANINST):

    def __init__(self, addr, **kwargs):
        LANINST.__init__(self, addr, **kwargs)
        self.timeout = 5000
        self.measurements = {}

    def new_measurement(self, name, wafer=''):
        m = LRCMeasurement(name, wafer=wafer)
        self.measurements[m.name] = m

    def change_display(self, combination, p=True):
        code = 'A' + str(combination[0]) +'B' + str(combination[1])
        if code in display_combos.keys():
            self.ask('A' + str(combination[0]))
            self.ask('B' + str(combination[1]))
            if p:
                print display_combos[code]
        else:
            raise ValueError("Allowed arguments: ([A] 1-4, [B] 1-3).")

    def circuit_mode(self, arg):
        if arg == 'auto':
            s = 'C1'
        elif arg == 'series':
            s = 'C2'
        elif arg == 'parallel':
            s = 'C3'
        else:
            raise ValueError("Invalid argument ('auto', 'series', or 'parallel').")
        self.ask(s)
        print circuit_mode[s]

    # These program codes can not be used if reference data is not stored
    def deviation_measurement(self, arg):
        if arg == 'off':
            s = 'D0'
        elif arg == 'delta':
            s = 'D1'
        elif arg == 'delta%':
            s = 'D2'
        else:
            raise ValueError("Invalid argument ('off', 'delta', or 'delta%').")
        self.ask(s)
        print deviation_measurement[s]

    def frequency_step(self, args, p=True):
        if args[0] == 10 and args[1] == 'kHz':
            s = 'F11'
        elif args[0] == 20 and args[1] == 'kHz':
            # 30 kHz in Option 004
            s = 'F12'
        elif args[0] == 40 and args[1] == 'kHz':
            # 50 kHz in Option 004
            s = 'F13'
        elif args[0] == 100 and args[1] == 'kHz':
            s = 'F14'
        elif args[0] == 200 and args[1] == 'kHz':
            # 300 kHz in Option 004
            s = 'F15'
        elif args[0] == 400 and args[1] == 'kHz':
            # 500 kHz in Option 004
            s = 'F16'
        elif args[0] == 1 and args[1] == 'MHz':
            s = 'F17'
        elif args[0] == 2 and args[1] == 'MHz':
            # 3 MHz in Option 004
            s = 'F18'
        elif args[0] == 4 and args[1] == 'MHz':
            # 5 MHz in Option 004
            s = 'F19'
        elif args[0] == 10 and args[1] == 'MHz':
            s = 'F20'
        elif args == '*1':
            s = 'F21'
        elif args == '*2':
            s = 'F22'
        else:
            raise ValueError("Invalid arg.")
        self.ask(s)
        if p:
            print frequency_step[s]

    def high_resolution(self, arg):
        if arg == 'off':
            s = 'H0'
        elif arg == 'on':
            s = 'H1'
        else:
            raise ValueError("Invalid arg ('off' or 'on).")
        self.ask(s)
        print high_resolution[s]

    # If Data Ready is set to ON, SRQ signal is outputted when measurement data is provided.
    def data_ready(self, arg):
        if arg == 'off':
            s = 'I0'
        elif arg == 'on':
            s = 'I1'
        else:
            raise ValueError("Invalid arg ('off' or 'on).")
        self.ask(s)
        print data_ready[s]

    def multiplier(self, arg):
        if arg == 0.01:
            s = 'M1'
        elif arg == 0.1:
            s = 'M2'
        elif arg == 1:
            s = 'M3'
        else:
            raise ValueError('Allowed values: 0.01, 0.1, and 1.')
        self.ask(s)
        print multiplier[s]

    # depends on DISPLAY A, DISPLAY B and Measuring Frequency settings:
    # If range is set to a range which can not make the measurement, range is automatically reset to the nearest
    # range capable of making the measurement.
    def lcrz_range(self, args):
        if args == 'auto':
            s = 'R31'
        elif args == 'manual':
            s = 'R32'
        elif args[0] == '1000fF' and args[1] == '100nH':
            s = 'R11'
        elif args[0] == '10pF' and args[1] == '1000nH' and args[2] == '100mOhms':
            s = 'R12'
        elif args[0] == '100pF' and args[1] == '10uH' and args[2] == '10Ohms':
            s = 'R13'
        elif args[0] == '1000pF' and args[1] == '100uH' and args[2] == '100Ohms':
            s = 'R14'
        elif args[0] == '10nF' and args[1] == '100uH' and args[2] == '10kOhms':
            s = 'R15'
        elif args[0] == '100nF' and args[1] == '1mH' and args[2] == '100kOhms':
            s = 'R16'
        elif args[0] == '1000nF' and args[1] == '10mH' and args[2] =='10kOhms':
            s = 'R17'
        elif args[0] == '10uF' and args[1] == '1000mH' and args[2] == '1000kOhms':
            s = 'R18'
        elif args[0] == '100uF' and args[1] == '10H' and args[2] == '10MOhms':
            s = 'R19'
        elif args[1] == '100H':
            s = 'R20'
        else:
            print 'Allowed arguments in list form (no spaces between number and units: '
            for key in lcrz_range.keys():
                print lcrz_range[key]
            raise ValueError()
        self.ask(s)
        print lcrz_range[s]

    # This program code can not be used if reference data is not stored.
    def recall_ref_value(self):
        print self.ask('RE').strip()

    def self_test(self, arg):
        if arg == 'off':
            s = 'S0'
        elif arg == 'on':
            s = 'S1'
        else:
            raise ValueError("Arg is either 'off' or 'on'")
        self.ask(s)
        print self_test[s]

    def store_ref_value(self):
        self.ask('ST')

    # When external trigger is used, set the 4275a to local by pressing the LOCAL key
    def trigger(self, arg):
        if arg == 'int':
            s = 'T1'
        elif arg == 'ext':
            s = 'T2'
        elif arg == 'hold' or arg == 'manual':
            s = 'T3'
        else:
            raise ValueError("Allowed args: 'int', 'ext', and 'hold' or 'manual'.")
        self.ask(s)
        print trigger[s]

    def zero(self, arg):
        if arg == 'open':
            s = 'Z0'
        elif arg == 'short':
            s = 'ZS'
        else:
            raise ValueError("Allowed args: 'open' and 'short'.")
        self.ask(s)
        print zero[s]

    # This program code is used to trigger the instrument
    def execute(self):
        self.ask('E')

    # This program code can be used to recognize the state of key settings.
    def key_state_out(self):
        rstr = self.ask('K').strip()
        print 'Display Combination: ' + display_combos[rstr[:4]]
        print 'Circuit Mode: ' + circuit_mode[rstr[4:6]]
        print 'Deviation Measurement: ' + deviation_measurement[rstr[6:8]]
        print 'Frequency Step: ' + frequency_step[rstr[8:11]]
        print 'High Resolution: ' + high_resolution[rstr[11:13]]
        print 'Data Ready: ' + data_ready[rstr[13:15]]
        print 'Multiplier: ' + multiplier[rstr[15:17]]
        print 'LCRZ Range: ' + lcrz_range[rstr[17:20]]
        print 'Self Test: ' + self_test[rstr[20:22]]
        print 'Trigger: ' + trigger[rstr[22:24]]

    def output_display(self):
        rstr = self.ask('C')
        formatted1 = float(rstr.split(',')[0][5:])
        formatted2 = float(rstr.split(',')[1][2:])
        # looks really dumb but this prevents outputting a negative zero
        # if formatted1 == 0.0:
        #     formatted1 = 0.0
        # if formatted2 == 0.0:
        #     formatted2 = 0.0
        return formatted1, formatted2, rstr

    def sweep(self):
        values = {}
        for freq in sweep_kHz:
            self.frequency_step((freq, 'kHz'), p=False)
            values[str(freq) + 'kHz'] = self.output_display()
        for freq in sweep_MHz:
            self.frequency_step((freq, 'MHz'), p=False)
            values[str(freq) + 'MHz'] = self.output_display()
        return values

    def sweep_z(self, m):
        self.change_display((4, 1), p=False)
        m.z = self.sweep()

    def sweep_cd(self, m):
        self.change_display((2, 1), p=False)
        m.cd = self.sweep()

    def sweep_cq(self, m):
        self.change_display((2, 2), p=False)
        m.cq = self.sweep()

    def sweep_cesr_g(self, m):
        self.change_display((2, 3), p=False)
        m.cesr_g = self.sweep()

    def sweep_ld(self, m):
        self.change_display((1, 1), p=False)
        m.ld = self.sweep()

    def sweep_lq(self, m):
        self.change_display((1, 2), p=False)
        m.lq = self.sweep()

    def sweep_lesr_g(self, m):
        self.change_display((1, 3), p=False)
        m.lesr_g = self.sweep()

    def sweep_rx_b(self, m):
        self.change_display((3, 1), p=False)
        m.rx_b = self.sweep()

    def sweep_rl_c(self, m):
        self.change_display((3, 2), p=False)
        m.rl_c = self.sweep()

    def full_measurement(self, m):
        self.sweep_z(m)
        self.sweep_cd(m)
        self.sweep_cq(m)
        self.sweep_cesr_g(m)
        self.sweep_ld(m)
        self.sweep_lq(m)
        self.sweep_lesr_g(m)
        self.sweep_rx_b(m)
        self.sweep_rl_c(m)

    def save_all(self):
        for m in self.measurements:
            m.save()


class LRCMeasurement(object):

    def __init__(self, name, wafer=''):
        self.wafer = wafer
        self.name = name
        self.z = {}
        self.cd = {}
        self.cq = {}
        self.cesr_g = {}
        self.ld = {}
        self.lq = {}
        self.lesr_g = {}
        self.rx_b = {}
        self.rl_c = {}

    def __str__(self):
        return self.wafer + '_' + self.name

    def __repr__(self):
        return self.__str__()

    def save(self):
        with open(self.wafer + '_' + self.name + '.csv', 'w') as csvfile:
            fieldnames = ['Frequency', 'f', '|Z|', unichr(0x3b8).encode('utf-8'), 'L1', 'D (L)', 'L2', 'Q (L)', 'L3',
                          'ESR/G (L)', 'C1', 'D (C)', 'C2', 'Q (C)', 'C3', 'ESR/G (C)', 'R1', 'X/B', 'R2', 'L/C']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for freq in self.z.keys():
                f = int(filter(str.isdigit, freq))
                if 'M' in freq:
                    f = f * 1000
                writer.writerow({'Frequency': freq, 'f': f, '|Z|': self.z[freq][0],
                                 unichr(0x3b8).encode('utf-8'): self.z[freq][1], 'L1': self.ld[freq][0],
                                 'D (L)': self.ld[freq][1], 'L2': self.lq[freq][0], 'Q (L)': self.lq[freq][1],
                                 'L3': self.lesr_g[freq][0], 'ESR/G (L)': self.lesr_g[freq][1],
                                 'C1': self.cd[freq][0], 'D (C)': self.cd[freq][1], 'C2': self.cq[freq][0],
                                 'Q (C)': self.cq[freq][1], 'C3': self.cesr_g[freq][0],
                                 'ESR/G (C)': self.cesr_g[freq][1], 'R1': self.rx_b[freq][0],
                                 'X/B': self.rx_b[freq][1], 'R2': self.rl_c[freq][0], 'L/C': self.rl_c[freq][1]})
