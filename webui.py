import os
import time
import signal
import argparse
from interpolate_engine import InterpolateEngine
from webui_utils.simple_log import SimpleLog
from webui_utils.simple_config import SimpleConfig
from webui_utils.file_utils import create_directories
from create_ui import setup_ui
from webui_events import WebuiEvents
from webui_tips import WebuiTips

def main():
    global prevent_inbrowser
    parser = argparse.ArgumentParser(description='VFIformer Web UI')
    parser.add_argument("--config_path", type=str, default="config.yaml", help="path to config YAML file")
    parser.add_argument("--verbose", dest="verbose", default=False, action="store_true", help="Show extra details")
    args = parser.parse_args()
    log = SimpleLog(args.verbose)
    config = SimpleConfig(args.config_path).config_obj()
    create_directories(config.directories)
    WebuiTips.set_tips_path(config.user_interface["tips_path"])
    engine = InterpolateEngine(config.model, config.gpu_ids)
    webui_events = WebuiEvents(engine, config, log)
    while True:
        print("Starting VFIformer-WebUI")
        print("Please be patient, the models are loaded on the first interpolation")
        app = setup_ui(config, webui_events, restart_app)
        app.launch(inbrowser = config.auto_launch_browser and not prevent_inbrowser,
                    server_name = config.server_name,
                    server_port = config.server_port,
                    prevent_thread_lock=True)
        # idea borrowed from stable-diffusion-webui webui.py
        # after initial launch, disable inbrowser for subsequent restarts
        prevent_inbrowser = True
        wait_on_server(app)
        print("\n--- Restarting\n")

restart = False
prevent_inbrowser = False

def restart_app():
    global restart
    restart = True

#### code borrowed from stable-diffusion-webui webui.py:
def wait_on_server(app):
    global restart
    while True:
        time.sleep(0.5)
        if restart:
            restart = False
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
