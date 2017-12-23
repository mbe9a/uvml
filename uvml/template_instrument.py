"""
Mike Eller
UVML
November 2017
"""

from vxi11 import Instrument


class LANINST(Instrument):

	def __init__(self, addr, ip="10.160.102.249", gpib=True, gpib_addr=0):
		if gpib:
			Instrument.__init__(self, ip, "gpib" + str(gpib_addr) + "," + str(addr))
		else:
			raise NotImplementedError

	def id(self):
		print self.ask("*IDN?")

