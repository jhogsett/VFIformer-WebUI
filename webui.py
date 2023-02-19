import os
import time
import signal
import argparse
from typing import Callable
from interpolate_engine import InterpolateEngine
from webui_utils.simple_log import SimpleLog
from webui_utils.simple_config import SimpleConfig
from webui_utils.file_utils import create_directories
from create_ui import create_ui
from webui_tips import WebuiTips

def main():
    parser = argparse.ArgumentParser(description='VFIformer Web UI')
    parser.add_argument("--config_path", type=str, default="config.yaml", help="path to config YAML file")
    parser.add_argument("--verbose", dest="verbose", default=False, action="store_true", help="Show extra details")
    args = parser.parse_args()
    log = SimpleLog(args.verbose)
    config = SimpleConfig(args.config_path).config_obj()
    create_directories(config.directories)
    WebUI(config, log.log).start()

class WebUI:
    def __init__(self,
                    config : SimpleConfig,
                    log_fn : Callable):
        self.config = config
        self.log_fn = log_fn
        self.restart = False
        self.prevent_inbrowser = False

    def start(self):
        WebuiTips.set_tips_path(self.config.user_interface["tips_path"])
        engine = InterpolateEngine(self.config.model, self.config.gpu_ids)
        while True:
            print("\nStarting VFIformer-WebUI")
            print("Models are loaded on the first interpolation")
            app = create_ui(self.config, engine, self.log_fn, self.restart_app)
            app.launch(inbrowser = self.config.auto_launch_browser and not self.prevent_inbrowser,
                        server_name = self.config.server_name,
                        server_port = self.config.server_port,
                        prevent_thread_lock=True)
            # after initial launch, disable inbrowser for subsequent restarts
            self.prevent_inbrowser = True
            self.wait_on_server(app)
            print("\n--- Restarting\n")

    def restart_app(self):
        self.restart = True

    def wait_on_server(self, app):
        while True:
            time.sleep(0.5)
            if self.restart:
                self.restart = False
                time.sleep(0.5)
                app.close()
                time.sleep(0.5)
                break

# make the program just exit at ctrl+c without waiting for anything
def sigint_handler(sig, frame):
    print(f'Interrupted with signal {sig} in {frame}')
    os._exit(0)
signal.signal(signal.SIGINT, sigint_handler)

if __name__ == '__main__':
    main()
