from template_instrument import LANINST

class Keithley(LANINST):

	@property
	def on(self):
		return self._on

	@on.setter
	def on(self, value):
		self._on = bool(value)
		self.output()

	def __init__(self, addr, **kwargs):
		LANINST.__init__(self, addr, **kwargs)
		self._on = False
		self.output()

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

	def output(self):
		if self._on:
			self.write(":outp:stat 1")
		else:
			self.write(":outp:stat 0")

	def measure_function(self, voltage=False, current=False):
		if voltage and current:
			self.write(":SENS:FUNC  'VOLT', 'CURR'")
		elif voltage:
			self.write(":SENS:FUNC  'VOLT'")
		elif current:
			self.write(":SENS:FUNC  'CURR'")
	
	def measure(self):
		if self.on:
			print self.ask("read?")
		else:
			return "Not permitted with output off."
