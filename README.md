# Test Equipment

Python drivers for my benchtop test equipment

These provide simple python drivers for some of my instruments:
 * HDM3000 Digital multimeter
 * IT6302 Power supply
 * SDG2082 Signal generator
 * TENMA72-132 Electronic load

These can be used with simple python bindings such as:

```python
from instrument.HDM3000 import HDM3000

dmm = HDM3000()
dmm.set_remote(True)

voltage = dmm.get_voltage()

dmm.close()
```

# SCPI transport

Each of these instruments contains a reference to a `SCPI` object.

The SCPI object provides an interface to send and recieve SCPI commands to the instrument. The following transport layers are supported:
 * TTY/Serial
 * TCP
 * UDP

When calling a constructor for an instrument, a SCPI URI is used to specify the location and transport mechanism. The URI contains 3 components:
1. Transport specifier
2. Address
3. Optional argument

The general format is `<transport>://<address>[:<argument>]`

## TTY
This specifies a COM port. The baud rate will be selected by the instrument, but can be overridden by the argument.

 * `tty://COM3` specifies a serial port on `COM3`
 * `tty://COM3:115200` explicitly selects 115200 baud.

## Sockets

SCPI sockets may be TCP or UDP. The argument specifies the destination port. The destination port defaults to 5025 on most instruments.

* `tcp://192.168.1.100` specifies a tcp socket
* `udp://192.168.1.100` specifies a udp socket
* `ip://192.168.1.100` lets the instrument select `tcp` or `udp`
* `tcp://phoenix.local` address names are valid
* `udp://192.168.1.100:5025` explitictly selects port 5025

## Creating devices

The following shows examples of connecting to an instrument.

```python
from instrument.TENMA72_132 import TENMA72_132

# 1. Using its known location
eload = TENMA72_132("ip://192.168.1.100")

# 2. Some IP based instruments can be scanned for
devices = TENMA72_132.find_devices()
print(devices) # [udp://192.168.1.100:5025]
eload = TENMA72_132(devices[0])

# 3. Most instruments have defaults which will find them automatically
eload = TENMA72_132() # Normally equivalent to IT6302(IT6302.find_devices(1)[0])

# 4. Using a manually constructed SCPI object
from instrument.SCPI import SocketSCPI
scpi = SocketSCPI("192.168.1.100", 5025, is_tcp = False)
eload = TENMA72_132(scpi)
```

# General patterns

The instruments are not individually documented. The methods are annotated, and I hope inspection of the methods will be enough for anyone familar with the instrument.

The following example shows some common patterns:

```python
from instrument.IT6302 import IT6302

psu = IT6302()

# This checks that your instrument responds to an identification request.
# This is an important sanity check.
psu.is_present(True)

# Most instruments needs to be put into remote mode for write operations to succeed
psu.set_remote(True)

# Most instruments have multiple channels. These will be 1 indexed (as per the front panel)
psu.select_channel(1)

# Inspect the annotations for specifics on its getters/setters
# SI units have been preferred.
psu.set_voltage(3.3)
psu.set_current(1.0)

# The input/output will need to be explicitly enabled
psu.set_output(True)

# This closes the SCPI transport gracefully.
# This will also exit remote mode where applicable
psu.close()
```

