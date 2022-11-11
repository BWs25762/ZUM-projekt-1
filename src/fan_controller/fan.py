from enum import Enum
from typing import List
from timeit import default_timer as timer
from math import sin


class RegisterList:
    def _read_registers(self) -> List[str]:
        with open(self.ec_address, "rb") as f:
            content = f.read()
        registers_list = content.hex('-').split('-')
        return registers_list

    def __init__(self, ec_address: str):
        self.ec_address = ec_address
        self.registers = self._read_registers()

    def read_register(self, address: int) -> int:
        return int(self.registers[address], 16)

    def write_register(self, value: int, address: int) -> None:
        write_val = ('0' + hex(value).replace('0x', ''))[-2:]
        self.registers[address] = write_val

    def write_changes(self):
        registers_string = ' '.join(self.registers)
        registers_bytes = bytes.fromhex(registers_string)
        with open(self.ec_address, "wb") as f:
            f.write(registers_bytes)

    def update(self):
        self.registers = self._read_registers()


class MockRegisterList:
    def _read_registers(self) -> List[int]:
        return [0 for _ in range(255)]

    def __init__(self):
        self.registers: List[int] = self._read_registers()

    def read_register(self, address: int) -> int:
        if address == 0:
            t = int(255 * (sin(timer() / 10) + 1) / 2)
            print(f"t: {t}")
            return t
        return self.registers[address]

    def write_register(self, value: int, address: int) -> None:
        self.registers[address] = value

    def write_changes(self):
        pass

    def update(self):
        pass


class Register:
    def __init__(self, address: int, register_list: RegisterList):
        self.address = address
        self.register_list = register_list

    # @staticmethod
    # def __serialize_value__(stdout_val: bytes):
    #     str_val = stdout_val.decode('utf-8')
    #     int_val = int(str_val.split(' ')[0])
    #     return int_val

    def read(self) -> int:
        return self.register_list.read_register(self.address)

    def write(self, value: int):
        self.register_list.write_register(value, self.address)


class Modes(Enum):
    AUTO = "auto"
    MANUAL = "manual"


class ModeRegister(Register):
    def __init__(self, address: int, register_list: RegisterList, manual_value: int, auto_value: int) -> None:
        super().__init__(address, register_list)
        self.manual_value: int = manual_value
        self.auto_value = auto_value

    def __set_auto__(self):
        self.write(self.auto_value)

    def __set_manual__(self):
        self.write(self.manual_value)

    def set_mode(self, mode: Modes):
        mode_register = {
            Modes.AUTO: self.__set_auto__,
            Modes.MANUAL: self.__set_manual__
        }
        mode_register[mode]()


class FanRegister(Register):
    def __init__(self, address: int, register_list: RegisterList, min: int, max: int) -> None:
        super().__init__(address, register_list)
        self.min: int = min
        self.max: int = max


class Fan:
    RESOLUTION = 50

    @classmethod
    def from_dict(cls, config: dict, register_list: RegisterList, max_temp: int):
        name = config["name"]
        mode_configs = config["mode"]
        mode_registers = []
        for mode_config in mode_configs:
            mode_register = ModeRegister(
                address=mode_config["register"],
                register_list=register_list,
                manual_value=mode_config["manual"],
                auto_value=mode_config["auto"]
            )
            mode_registers.append(mode_register)
        fan_read_registers: List[FanRegister] = []
        read_configs = config["read"]
        for read_config in read_configs:
            read_register = FanRegister(
                address=read_config["register"],
                register_list=register_list,
                min=read_config["min"],
                max=read_config["max"]
            )
            fan_read_registers.append(read_register)
        fan_write_registers: List[FanRegister] = []
        write_configs = config["write"]
        for write_config in write_configs:
            write_register = FanRegister(
                address=write_config["register"],
                register_list=register_list,
                min=write_config["min"],
                max=write_config["max"]
            )
            fan_write_registers.append(write_register)
        temp_register = FanRegister(
            address=config["temp"],
            register_list=register_list,
            min=0,
            max=max_temp
        )
        fan = cls(
            name,
            mode_registers,
            fan_read_registers,
            fan_write_registers,
            temp_register
        )
        return fan

    def __init__(
            self,
            name: str,
            mode_register: List[ModeRegister],
            fan_read_registers: List[FanRegister],
            fan_write_registers: List[FanRegister],
            temperature_register: FanRegister
    ) -> None:
        self.name: str = name
        self._mode: List[ModeRegister] = mode_register
        self._read_list: List[FanRegister] = fan_read_registers
        self._write_list: List[FanRegister] = fan_write_registers
        self._temp: FanRegister = temperature_register
        self._history_len = 500
        self._read_history: List[List[int]] = [[] for _ in self._read_list]
        self._temperature_history: List[int] = []

    def map_value(self, value, range_min, range_max):
        return int(((value - range_min) / (range_max - range_min)) * self.RESOLUTION)

    def unmap_value(self, value, range_min, range_max):
        return int(((value * (range_max - range_min)) / self.RESOLUTION) + range_min)

    @property
    def modes(self):
        return self._mode

    @property
    def read_registers(self):
        return self._read_list

    @property
    def write_registers(self):
        return self._write_list

    @property
    def temperature_register(self):
        return self._temp

    @property
    def history_length(self):
        return self.history_length

    @history_length.setter
    def history_length(self, length: int):
        self._history_len = length

    def read_temperature(self):
        return self._temp.read()

    @property
    def temperature_history(self):
        temperature = self.read_temperature()
        self._temperature_history.append(temperature)
        index = len(self._temperature_history) - self._history_len if len(self._temperature_history) > self._history_len else 0
        self._temperature_history = self._temperature_history[index:]
        return self._temperature_history

    def read_speeds(self):
        speeds = [r.read() for r in self._read_list]
        return speeds

    @property
    def read_history(self):
        speeds = self.read_speeds()
        for i, hist in enumerate(self._read_history):
            hist.append(speeds[i])
            index = len(hist) - self._history_len if len(hist) > self._history_len else 0
            hist = hist[index:]
            self._read_history[i] = hist
        return self._read_history

    def set_speed(self, speed: float):
        speed = int(speed * self.RESOLUTION)
        for i, write in enumerate(self._write_list):
            self._mode[i].set_mode(Modes.MANUAL)
            unmapped_speed = self.unmap_value(speed, write.min, write.max)
            write.write(unmapped_speed)

    def set_mode(self, mode: Modes):
        for mode_r in self._mode:
            mode_r.set_mode(mode)

    @property
    def speed_level(self):
        speeds = self.read_speeds()
        mapped_speeds = []
        for i, read in enumerate(self._read_list):
            mapped_speeds.append(float(self.map_value(speeds[i], read.min, read.max)) / self.RESOLUTION)
        return sum(mapped_speeds)/len(mapped_speeds)


def build_fans_from_config(config: dict, register_list: RegisterList) -> List[Fan]:
    fan_configs = config["fans"]
    max_temp = int(config["max_temp"])
    fan_list: List[Fan] = [Fan.from_dict(fan_config, register_list, max_temp) for fan_config in fan_configs]
    return fan_list
