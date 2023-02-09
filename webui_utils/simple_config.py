from collections import namedtuple
import yaml

class SimpleConfig:
    def __new__(cls, path : str = "config.yaml"):
        if not hasattr(cls, 'instance'):
            cls.instance = super(SimpleConfig, cls).__new__(cls)
            cls.instance.init(path)
        return cls.instance

    def init(self, path : str):
        with open(path, encoding="utf-8") as file:
            self.config = yaml.load(file, Loader=yaml.FullLoader)

    def get(self, key : str):
        return self.config[key]

    def config_obj(self):
        return namedtuple("ConfigObj", self.config.keys())(*self.config.values())
