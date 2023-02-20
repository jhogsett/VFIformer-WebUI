import gradio as gr
from webui_utils.simple_icons import SimpleIcons
from tabs.frame_interpolation import FrameInterpolation
from tabs.frame_search import FrameSearch
from tabs.video_inflation import VideoInflation
from tabs.resynthesize_video import ResynthesizeVideo
from tabs.frame_restoration import FrameRestoration
from tabs.video_blender import VideoBlender
from tabs.mp4_to_png import MP4toPNG
from tabs.png_to_mp4 import PNGtoMP4
from tabs.gif_to_png import GIFtoPNG
from tabs.png_to_gif import PNGtoGIF
from tabs.resequence_files import ResequenceFiles
from tabs.change_fps import ChangeFPS
from tabs.future import Future
from tabs.options import Options
from tabs.resources import Resources

def create_ui(config, engine, log_fn, restart_fn):
    with gr.Blocks(analytics_enabled=False,
                    title="VFIformer Web UI",
                    theme=config.user_interface["theme"],
                    css=config.user_interface["css_file"]) as app:
        gr.HTML(SimpleIcons.MOVIE + "VFIformer Web UI", elem_id="appheading")
        FrameInterpolation(config, engine, log_fn).render_tab()
        FrameSearch(config, engine, log_fn).render_tab()
        VideoInflation(config, engine, log_fn).render_tab()
        ResynthesizeVideo(config, engine, log_fn).render_tab()
        FrameRestoration(config, engine, log_fn).render_tab()
        VideoBlender(config, engine, log_fn).render_tab()
        with gr.Tab(SimpleIcons.WRENCH + "Tools"):
            with gr.Tab(SimpleIcons.FOLDER + "File Conversion"):
                gr.HTML("Tools for common video file conversion tasks (ffmpeg.exe must be in path)", elem_id="tabheading")
                MP4toPNG(config, engine, log_fn).render_tab()
                PNGtoMP4(config, engine, log_fn).render_tab()
                GIFtoPNG(config, engine, log_fn).render_tab()
                PNGtoGIF(config, engine, log_fn).render_tab()
            ResequenceFiles(config, engine, log_fn).render_tab()
            ChangeFPS(config, engine, log_fn).render_tab()
            Future(config, engine, log_fn).render_tab()
            Options(config, engine, log_fn, restart_fn).render_tab()
            Resources(config, engine, log_fn, restart_fn).render_tab()
        footer = SimpleIcons.COPYRIGHT + ' 2023 J. Hogsett  •  <a href="https://github.com/jhogsett/VFIformer-WebUI">Github</a>  •  <a href="https://github.com/dvlab-research/VFIformer">VFIformer</a>  •  <a href="https://gradio.app">Gradio</a>  •  <a href="/" onclick="javascript:gradioApp().getElementById(\'settings_restart_gradio\').click(); return false">Reload UI</a>'
        gr.HTML(footer, elem_id="footer")
    return app
