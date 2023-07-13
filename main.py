from equipment.TENMA72_132 import TENMA72_132
from equipment.HDM3000 import HDM3000
from equipment.IT6300 import IT6300
from equipment.SDG2000 import SDG2000

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
