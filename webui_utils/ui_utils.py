from .simple_utils import max_steps, restored_frame_fractions, restored_frame_predictions, fps_change_details

def update_splits_info(num_splits : float):
    return str(max_steps(num_splits))

def update_info_fr(num_frames : int, num_splits : int):
    fractions = restored_frame_fractions(num_frames)
    predictions = restored_frame_predictions(num_frames, num_splits)
    return fractions, predictions

def update_info_fc(starting_fps : int, ending_fps : int, precision : int):
    return fps_change_details(starting_fps, ending_fps, precision)

def create_report(info_file : str, img_before_file : str, img_after_file : str, num_splits : int, output_path : str, output_paths : list):
    report = f"""before file: {img_before_file}
after file: {img_after_file}
number of splits: {num_splits}
output path: {output_path}
frames:
""" + "\n".join(output_paths)
    with open(info_file, 'w', encoding='utf-8') as f:
        f.write(report)
