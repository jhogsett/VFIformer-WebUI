import yaml
from collections import namedtuple

class SimpleConfig:
    def __new__(cls, path : str = "config.yaml"):
        if not hasattr(cls, 'instance'):
            cls.instance = super(SimpleConfig, cls).__new__(cls)
            cls.instance.init(path)
        return cls.instance

    def init(self, path : str):
        with open(path) as f:
            self.config = yaml.load(f, Loader=yaml.FullLoader)

    def get(self, key : str):
        return self.config[key]

    def config_obj(self):
        return namedtuple("ConfigObj", self.config.keys())(*self.config.values())
