from typing import List

from fan_controller.fan import Fan

import numpy as np


class ViewController:

    @staticmethod
    def represent_value(val: int, resolution: int):
        values = {
            'filler': '█',
            'empty': ' ',
            0: " ",
            1: "▁",
            2: "▂",
            3: "▃",
            4: "▄",
            5: "▅",
            6: "▆",
            7: "▇",
            8: "█",
        }
        values_len = len(values) - 2
        max_multiplier = int(resolution / values_len)
        multiplier = int(val / values_len)
        residual = val % values_len
        base = multiplier * [values["filler"]]
        out = (max_multiplier - multiplier) * [values['empty']] + [values[residual]] + base
        return out

    def serialize_history(self, history, range_min, range_max, resolution):
        mapped = [int(((val - range_min) / (range_max - range_min)) * resolution) for val in history]
        represented = np.array([self.represent_value(val, resolution) for val in mapped])
        represented = np.transpose(represented)
        out = ""
        for i in represented:
            out += ''.join(i)
            out += '\n'
        return out

    def get_fan_representation(self, fan: Fan):
        out = f"{fan.name}\n" \
              f"temperature:\n"
        temp_graph = self.serialize_history(
            fan.temperature_history,
            fan.temperature_register.min,
            fan.temperature_register.max,
            fan.RESOLUTION
        )
        out += temp_graph + "\n"
        read_histories = fan.read_history
        for i, read_register in enumerate(fan.read_registers):
            out += f"fan {i+1}:\n"
            register_graph = self.serialize_history(
                read_histories[i],
                read_register.min,
                read_register.max,
                fan.RESOLUTION
            )
            out += register_graph + "\n"
        return out
