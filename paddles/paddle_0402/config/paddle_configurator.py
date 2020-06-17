from configparser import ConfigParser
from pathlib import Path
from typing import List, Any

true_path = Path(__file__).parent / 'config.ini'
_parser = ConfigParser()
_parser.read(str(true_path.resolve()), encoding='utf-8')


class Config(object):
    @staticmethod
    def get_property_string(section_name: str, property_name: str) -> Any:
        return _parser.get(section_name, property_name)

    @staticmethod
    def get_property_int(section_name: str, property_name: str) -> Any:
        return _parser.getint(section_name, property_name)

    @staticmethod
    def get_property_float(section_name: str, property_name: str) -> Any:
        return _parser.getfloat(section_name, property_name)

    @staticmethod
    def get_property_bool(section_name: str, property_name: str) -> Any:
        return _parser.getboolean(section_name, property_name)


class NmistRawAnnConfig(Config):
    @property
    def network_size(self) -> List[int]:
        layer_size_string = Config.get_property_string('nmist_raw_ann', 'layer_sizes')
        return eval(layer_size_string)

    @property
    def gradient_step_size(self) -> float:
        return Config.get_property_float('nmist_raw_ann', 'gradient_step_size')

    @property
    def regularization_lambda(self) -> float:
        return Config.get_property_float('nmist_raw_ann', 'regularization_lambda')

    @property
    def training_iterations(self) -> int:
        return Config.get_property_int('nmist_raw_ann', 'num_training_iterations')

nmist_raw_ann_config = NmistRawAnnConfig()