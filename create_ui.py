import gradio as gr
from webui_utils.simple_icons import SimpleIcons
from tabs.frame_interpolation import frame_interpolation_tab
from tabs.frame_search import frame_search_tab
from tabs.video_inflation import video_inflation_tab
from tabs.resynthesize_video import resynthesize_video_tab
from tabs.frame_restoration import frame_restoration_tab
from tabs.video_blender import video_blender_tab
from tabs.mp4_to_png import mp4_to_png_tab
from tabs.png_to_mp4 import png_to_mp4_tab
from tabs.gif_to_png import gif_to_png_tab
from tabs.png_to_gif import png_to_gif_tab
from tabs.resequence_files import resequence_files_tab
from tabs.change_fps import change_fps_tab
from tabs.future import future_tab
from tabs.options import options_tab

def create_ui(config, webui_events, restart_fn):
    e = {}
    gr.HTML(SimpleIcons.MOVIE + "VFIformer Web UI", elem_id="appheading")
    e.update(frame_interpolation_tab(config, webui_events, e))
    e.update(frame_search_tab(config, webui_events, e))
    e.update(video_inflation_tab(config, webui_events, e))
    e.update(resynthesize_video_tab(config, webui_events, e))
    e.update(frame_restoration_tab(config, webui_events, e))
    e.update(video_blender_tab(config, webui_events, e))
    with gr.Tab(SimpleIcons.WRENCH + "Tools"):
        with gr.Tab(SimpleIcons.FOLDER + "File Conversion"):
            gr.HTML("Tools for common video file conversion tasks (ffmpeg.exe must be in path)", elem_id="tabheading")
            e.update(mp4_to_png_tab(config, webui_events, e))
            e.update(png_to_mp4_tab(config, webui_events, e))
            e.update(gif_to_png_tab(config, webui_events, e))
            e.update(png_to_gif_tab(config, webui_events, e))
        e.update(resequence_files_tab(config, webui_events, e))
        e.update(change_fps_tab(config, webui_events, e))
        e.update(future_tab(config, webui_events, e))
        e.update(options_tab(config, webui_events, e, restart_fn))

    footer = SimpleIcons.COPYRIGHT + ' 2023 J. Hogsett  •  <a href="https://github.com/jhogsett/VFIformer-WebUI">Github</a>  •  <a href="https://github.com/dvlab-research/VFIformer">VFIformer</a>  •  <a href="https://gradio.app">Gradio</a>  •  <a href="/" onclick="javascript:gradioApp().getElementById(\'settings_restart_gradio\').click(); return false">Reload UI</a>'
    gr.HTML(footer, elem_id="footer")
    return e

def setup_ui(config, webui_events, restart_fn):
    with gr.Blocks(analytics_enabled=False,
                    title="VFIformer Web UI",
                    theme=config.user_interface["theme"],
                    css=config.user_interface["css_file"]) as app:
        create_ui(config, webui_events, restart_fn)
    return app
