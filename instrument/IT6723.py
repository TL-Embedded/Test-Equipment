from . import SCPI

class IT6723():
    def __init__(self, uri: str = "ip://it6723.local"):
        self.scpi = SCPI.from_uri(uri)
    
    def is_present(self, throw_on_error: bool = False) -> bool:
        # ITECH Electronics, IT6723B, 800756013807510010,  1.18-1.05
        success = self.scpi.get_idn().startswith("ITECH Electronics, IT6723")
        if throw_on_error and not success:
            raise Exception("IT6723 not found")
        return success

    def close(self):
        self.set_remote(False)
        self.scpi.close()

    def set_remote(self, is_remote: bool):
        mode = "REM" if is_remote else "LOC"
        self.scpi.write(f"SYST:{mode}")

    def get_voltage(self) -> float:
        return float(self.scpi.query("MEAS:VOLT?"))

    def get_current(self) -> float:
        return float(self.scpi.query("MEAS:CURR?"))
    
    def set_voltage(self, volts) -> float:
        self.scpi.write(f"VOLT {volts:.3f}V")
    
    def set_current(self, amps: float):
        self.scpi.write(f"CURR {amps:.3f}A")

    def set_output(self, is_on: bool):
        self.scpi.write(f"OUTP {1 if is_on else 0}")

