import logging
import os
import time
from typing import List

from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC

from command_recorder import CommandRecorder
from fan_controller.fan import RegisterList, build_fans_from_config, Fan, Modes
from fan_controller.view import ViewController
from language_decoder_builder import LanguageDecoderBuilder
from utils import get_data_dir, get_config


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
        self.register_list = RegisterList(ec_address=self.config["ec_address"])
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
            "kart??": "GPU",
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
        if setting == "??rednio":
            for fan in target_fan:
                fan.set_speed(0.5)
        if setting == "zero":
            for fan in target_fan:
                fan.set_speed(0.0)
        if setting == "dziesi????":
            for fan in target_fan:
                fan.set_speed(0.1)
        if setting == "dwadzie??cia":
            for fan in target_fan:
                fan.set_speed(0.2)
        if setting == "trzydzie??ci":
            for fan in target_fan:
                fan.set_speed(0.3)
        if setting == "czterdzie??ci":
            for fan in target_fan:
                fan.set_speed(0.4)
        if setting == "pi????dziesi??t":
            for fan in target_fan:
                fan.set_speed(0.5)
        if setting == "sze????dziesi??t":
            for fan in target_fan:
                fan.set_speed(0.6)
        if setting == "siedemdziesi??t":
            for fan in target_fan:
                fan.set_speed(0.7)
        if setting == "osiemdziesi??t":
            for fan in target_fan:
                fan.set_speed(0.8)
        if setting == "dziewi????dziesi??t":
            for fan in target_fan:
                fan.set_speed(0.9)
        if setting == "sto":
            for fan in target_fan:
                fan.set_speed(1.0)

    def manual_command_executor(self, args):
        command = input("provide command\n")
        self.parse_command(command)

    def wyjd??_command_executor(self, args):
        exit()

    def parse_command(self, command: str):
        command_executors = {
            "ustaw": self.ustaw_command_executor,
            "manualnie": self.manual_command_executor,
            "wyj??cie": self.wyjd??_command_executor
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
            print(previous_command)
            command = self.command_recorder.record_command()
            print(command)
            previous_command = command
            self.parse_command(command)



if __name__ == "__main__":
    mc = MainController()
    mc.main_loop()
