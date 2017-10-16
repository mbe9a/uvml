from vxi11 import Instrument

class LANINST(Instrument):

	def __init__(self, addr, ip="10.160.102.249", gpib=True, gpib_addr=0):
		if gpib:
			Instrument.__init__(ip, "gpib" + gpib_addr + "," + addr)
		else:
			raise NotImplementedError
