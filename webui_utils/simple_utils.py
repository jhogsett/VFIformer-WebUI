import math
from collections import namedtuple
from fractions import Fraction
from .simple_icons import SimpleIcons

# Computing the count of work steps needed based on the number of splits:
# Before splitting, there's one existing region between the before and after frames.
# Each split doubles the number of regions.
# Work steps = the final number of regions - the existing region.
def max_steps(num_splits : int) -> int:
    return 2 ** num_splits - 1

# Create an object with properies like what argparse provides
# Useful if using 3rd-party code expecting an args object
def FauxArgs(**kwargs):
    return namedtuple("FauxArgs", kwargs.keys())(**kwargs)

# True if target range is entirely within the domain range, inclusive
def float_range_in_range(target_min : float, target_max : float, domain_min : float, domain_max : float, use_midpoint=False):
    if use_midpoint:
        target = target_min + (target_max - target_min) / 2.0
        if target >= domain_min and target <= domain_max:
            return True
        else:
            return False
    else:
        if target_min >= domain_min and target_max <= domain_max:
            return True
        else:
            return False

# For Frame Search, given a frame time 0.0 - 1.0
# and a search precision (split count) compute the fractional
# time that will actually be found
def predict_search_frame(num_splits : int, fractional_time : float) -> float:
    resolution = 2 ** num_splits
    return round(resolution * fractional_time) / resolution

# For Frame Restoration, given a count of restored frames
# compute the frame search times for the new frames that will be created
def restored_frame_searches(restored_frame_count : int) -> list:
    return [(n + 1.0) / (restored_frame_count + 1.0) for n in range(restored_frame_count)]

# For Frame Restoration, given a count of restored frames
# compute a human friendly display of the fractional
# times for the new frames that will be created
def restored_frame_fractions(restored_frame_count : int) -> str:
    result = []
    for n in range(restored_frame_count):
        div = n + 1
        den = restored_frame_count + 1
        result.append(str(Fraction(div/den).limit_denominator()))
    return ", ".join(result)

# For Frame Restoration, given a count of restored frames
# and a precision (split count) compute the frames that
# are likely to be found given that precision
def restored_frame_predictions(restored_frame_count : int, num_splits : int) -> list:
    searches = restored_frame_searches(restored_frame_count)
    predictions = [str(predict_search_frame(num_splits, search)) for search in searches]

    # prepare to detect duplicates, including the outer frames
    all_frames = predictions + ["0.0"] + ["1.0"]

    warning = ""
    if len(set(all_frames)) != len(all_frames):
        warning = f" {SimpleIcons.WARNING} Repeated frames - increase precision"
    return ", ".join(predictions) + warning

def fps_change_details(starting_fps : int, ending_fps : int, precision : int):
    lowest_common_rate = math.lcm(starting_fps, ending_fps)
    expansion = int(lowest_common_rate / starting_fps)
    num_frames = expansion - 1
    sample_rate = int(lowest_common_rate / ending_fps)

    filled = num_frames
    sampled = f"1/{sample_rate}"

    if filled > 100:
        filled = str(filled) + " " + SimpleIcons.WARNING

    fractions = restored_frame_fractions(num_frames) or "n/a"
    predictions = restored_frame_predictions(num_frames, precision) or "n/a"
    return lowest_common_rate, filled, sampled, fractions, predictions
