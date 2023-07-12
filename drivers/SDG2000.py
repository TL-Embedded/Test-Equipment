from . import SCPI
import math
import time

class SDG2000():
    def __init__(self, uri: str):
        self.scpi = SCPI.from_uri(uri)
        self.selected_channel = 1
        self._ch = "C1"
        self._builtin_waves = None

    def is_present(self, throw_on_error: bool = False) -> bool:
        # Siglent Technologies,SDG2082X,SDG2XCAD5R3269,2.01.01.35R3B2
        success = self.scpi.get_idn().startswith("Siglent Technologies,SDG20")
        if throw_on_error and not success:
            raise Exception("HDM3055 not found")
        return success

    def close(self):
        self.scpi.close()

    def select_channel(self, ch: int):
        self.selected_channel = ch
        self._ch = f"C{ch}"

    def set_output(self, is_on: bool, load_ohms: float|None = None):
        load = f"{load_ohms:.0f}" if type(load_ohms) is float else "HZ"
        self.scpi.write(f"{self._ch}:OUTP {'ON' if is_on else 'OFF'},LOAD,{load}")

    def set_amplitude(self, amplitude_volts: float, offset_volts: float = 0.0):
        self._set_basic_wave([
            "AMP", f"{amplitude_volts:0.3f}V",
            "OFST", f"{offset_volts:0.3f}V",
        ])

    def set_span(self, min_volts: float, max_volts: float):
        self.set_amplitude( max_volts - min_volts, (max_volts + min_volts) / 2.0 )

    def set_frequency(self, frequency_hz: float, phase_deg: float = 0.0):
        self._set_basic_wave([
            "FRQ", f"{frequency_hz}HZ",
            "PHSE", f"{phase_deg:0.1f}",
        ])
    
    def set_wave_sine(self):
        self._set_basic_wave([
            "WVTP", "SINE",
        ])

    def set_wave_square(self, duty_percent: float = 50.0):
        self._set_basic_wave([
            "WVTP", "SQUARE",
            "DUTY", f"{duty_percent:0.1f}",
        ])

    def set_wave_dc(self):
        self._set_basic_wave([
            "WVTP", "DC",
        ])

    def set_wave_ramp(self, symmetry_percent: float = 50.0):
        self._set_basic_wave([
            "WVTP", "RAMP",
            "SYM", f"{symmetry_percent:0.1f}",
        ])

    def set_wave_noise(self, stddev_volts: float, bandwidth_hz: float|None = None):
        bw_params = [
            "BANDSTATE", "ON",
            "BANDWIDTH", f"{bandwidth_hz:f}",
        ] if bandwidth_hz else [
            "BANDSTATE", "OFF",
        ]
        self._set_basic_wave([
            "WVTP", "NOISE",
            "STDEV", f"{stddev_volts:0.3f}V",
        ] + bw_params)

    def set_wave_pulse(self, width_seconds: float = 1e-3, rise_seconds: float = 0.0):
        self._set_basic_wave([
            "WVTP", "PULSE",
            "WIDTH", f"{width_seconds:f}S",
            "RISE", f"{rise_seconds:f}S",
        ])
    
    def set_wave_arbitrary(self, name: str, user: bool = False, true_arb: bool = False):
        if user:
            self.scpi.write(f"{self._ch}:ARWV NAME,{name}")
        else: # builtin
            index = self._get_builtin_waves()[name]
            self.scpi.write(f"{self._ch}:ARWV INDEX,{index}")
        self.scpi.write(f"{self._ch}:SRATE MODE,{'TARB' if true_arb else 'DDS'}")

    def set_burst_cycles(self, period_seconds: float, cycles: int = 1):
        self.scpi.write(f"{self._ch}:BTWV STATE,ON,PRD,{period_seconds},GATE_NCYC,NCYC,TIME,{cycles}")

    def disable_burst(self):
        self.scpi.write(f"{self._ch}:BTWV STATE,OFF")

    def list_waves(self, user: bool = False) -> list[str]:
        if user:
            reply = self.scpi.query("STL? USER")
            return reply[4:].split(', ')
        else:
            return [name for name in self._get_builtin_waves()]

    def upload_user_wave(self, name: str, points: list[float]):
        payload = bytearray()
        for p in points:
            n = math.floor(p * 0x7FFF)
            n = self._sanitize_point(n) # required for early firmware.
            payload.append(n & 0xFF)
            payload.append((n >> 8) & 0xFF)
        command = f"C1:WVDT WVNM,{name},WAVEDATA,".encode()
        self.scpi.write_bytes(command + payload + bytes([0x0A]))
        time.sleep(0.5)

    def _sanitize_point(self, n: int) -> int:
        # Literally the dumbest garbage
        # Having an 0x0A ('\n') within a datapoint causes the command to be truncated.
        if (n & 0xFF00) == 0x0A00:
            if n > 0x0A7F:
                return 0x0B00
            else:
                return 0x09FF
        if (n & 0x00FF) == 0x000A:
            return n + 1
        return n

    def _set_basic_wave(self, params: list[str]):
        self.scpi.write(f"{self._ch}:BSWV {','.join(params)}")

    def _get_builtin_waves(self) -> dict[str, int]:
        if self._builtin_waves == None:
            reply = self.scpi.query("STL? BUILDIN")
            #STL M10, ExpFal, M100, ECG14...
            waves = {}
            parts = reply[4:].split(', ')
            for i in range(0, len(parts), 2):
                index = int(parts[i][1:])
                name = parts[i+1]
                waves[name] = index
            self._builtin_waves = waves
        return self._builtin_waves
    



