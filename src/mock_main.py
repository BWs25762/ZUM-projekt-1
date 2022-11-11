import json
import logging
import os
import time
from typing import List

from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC

from command_recorder import CommandRecorder
from fan_controller.fan import RegisterList, build_fans_from_config, Fan, Modes, MockRegisterList
from fan_controller.view import ViewController
from language_decoder_builder import LanguageDecoderBuilder
from utils import get_data_dir


def get_config():
    config_path = os.path.join(get_data_dir(), "mock_config.json")
    with open(config_path, "r") as f:
        config = json.load(f)
    return config

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"), force=True)


def build_language(language_decoder_builder: LanguageDecoderBuilder):
    if not os.path.exists(language_decoder_builder.language_model_path):
        language_decoder_builder.build_language()


class MainController:
    def _build_command_decoder(self, config: dict):
        processor: Wav2Vec2Processor = Wav2Vec2Processor.from_pretrained('facebook/wav2vec2-base-10k-voxpopuli-ft-pl')
        model: Wav2Vec2ForCTC = Wav2Vec2ForCTC.from_pretrained('facebook/wav2vec2-base-10k-voxpopuli-ft-pl')
        print("models created!")
        time.sleep(5)

        language_decoder_builder = LanguageDecoderBuilder(
            commands_dir=os.path.join(get_data_dir(), "commands"),
            language_dir=os.path.join(get_data_dir(), "language")
        )

        build_language(language_decoder_builder)

        decoder = language_decoder_builder.build_decoder(processor.tokenizer)

        command_recorder = CommandRecorder(
            volume_threshold=config["volume_threshold"],
            record_wait_time=config["record_wait_time"],
            initial_record_wait_time=config["initial_record_wait_time"],
            max_command_time=config["max_command_time"],
            decoder=decoder,
            processor=processor,
            model=model
        )
        return command_recorder

    def __init__(self):
        self.config = get_config()
        self.command_recorder = self._build_command_decoder(self.config)
        self.register_list = MockRegisterList()
        self.fans = build_fans_from_config(self.config, self.register_list)
        self.view_controller = ViewController()

    def get_fan(self, name: str):
        if name == "*":
            return self.fans
        for fan in self.fans:
            if fan.name == name:
                return [fan]
        raise RuntimeError(f"fan \"{name}\" not found!")

    def fan_faster_speed(self, fans: List[Fan]):
        for fan in fans:
            speed_level = fan.speed_level
            new_level = speed_level + 0.1
            final_level = new_level if new_level < 1.0 else 1.0
            fan.set_speed(final_level)

    def fan_slower_speed(self, fans: List[Fan]):
        for fan in fans:
            speed_level = fan.speed_level
            new_level = speed_level - 0.1
            final_level = new_level if new_level > 0.0 else 0.0
            fan.set_speed(final_level)

    def set_fans_auto(self, fans: List[Fan]):
        for fan in fans:
            fan.set_mode(Modes.AUTO)

    def ustaw_command_executor(self, args: list):
        if len(args) != 2:
            print("wrong argument amount!")
            return
        target, setting = args
        target_names = {
            "kartę": "GPU",
            "procesor": "CPU",
            "oba": "*"
        }
        target_fan = self.get_fan(target_names[target])
        if setting == "szybciej":
            self.fan_faster_speed(target_fan),
        if setting == "wolniej":
            self.fan_slower_speed(target_fan),
        if setting == "automatycznie":
            self.set_fans_auto(target_fan),
        if setting == "najszybciej":
            for fan in target_fan:
                fan.set_speed(1.0)
        if setting == "najwolniej":
            for fan in target_fan:
                fan.set_speed(0.0)
        if setting == "średnio":
            for fan in target_fan:
                fan.set_speed(0.5)
        if setting == "zero":
            for fan in target_fan:
                fan.set_speed(0.0)
        if setting == "dziesięć":
            for fan in target_fan:
                fan.set_speed(0.1)
        if setting == "dwadzieścia":
            for fan in target_fan:
                fan.set_speed(0.2)
        if setting == "trzydzieści":
            for fan in target_fan:
                fan.set_speed(0.3)
        if setting == "czterdzieści":
            for fan in target_fan:
                fan.set_speed(0.4)
        if setting == "pięćdziesiąt":
            for fan in target_fan:
                fan.set_speed(0.5)
        if setting == "sześćdziesiąt":
            for fan in target_fan:
                fan.set_speed(0.6)
        if setting == "siedemdziesiąt":
            for fan in target_fan:
                fan.set_speed(0.7)
        if setting == "osiemdziesiąt":
            for fan in target_fan:
                fan.set_speed(0.8)
        if setting == "dziewięćdziesiąt":
            for fan in target_fan:
                fan.set_speed(0.9)
        if setting == "sto":
            for fan in target_fan:
                fan.set_speed(1.0)

    def manual_command_executor(self, args):
        command = input("provide command\n")
        self.parse_command(command)

    def wyjdź_command_executor(self, args):
        exit()

    def parse_command(self, command: str):
        command_executors = {
            "ustaw": self.ustaw_command_executor,
            "manualnie": self.manual_command_executor,
            "wyjście": self.wyjdź_command_executor
        }
        command = command.strip()
        if command:
            command_list = command.split()
            command = command_list[0]
            args = command_list[1:]
            if command in command_executors.keys():
                command_executors[command](args)
                self.register_list.write_changes()

    def main_loop(self):
        previous_command = None
        while True:
            out = ""
            self.register_list.update()
            for fan in self.fans:
                out += self.view_controller.get_fan_representation(fan)
            os.system("clear")
            print(out)

            print(self.fans[0].read_temperature())
            print(previous_command)
            command = self.command_recorder.record_command()
            print(command)
            previous_command = command
            self.parse_command(command)



if __name__ == "__main__":
    mc = MainController()
    mc.main_loop()
