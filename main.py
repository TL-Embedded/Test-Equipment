from instrument.TENMA72_132 import TENMA72_132
from instrument.HDM3000 import HDM3000
from instrument.IT6300 import IT6300
from instrument.SDG2000 import SDG2000

psu = IT6300()
psu.is_present(True)
psu.select_channel(1)
print(psu.get_voltage())
psu.close()

eload = TENMA72_132()
eload.is_present(True)
print(eload.get_current())
eload.close()

dmm = HDM3000()
dmm.is_present(True)
print(dmm.get_voltage(10))
dmm.close()

sdg = SDG2000("ip://192.168.1.159")
sdg.is_present(True)
sdg.set_wave().span(0.0, 3.3).frequency(100).wave_pulse(1.5/1000).submit()
sdg.close()



