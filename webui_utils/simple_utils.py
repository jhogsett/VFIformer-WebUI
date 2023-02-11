from collections import namedtuple

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
# and a search depth (split count) compute the fractional
# time that will actually be found
def predict_search_frame(num_splits : int, fractional_time : float) -> float:
    resolution = 2 ** num_splits
    return round(resolution * fractional_time) / resolution

# For Frame Restoration, given a count of damaged frames
# compute a human friendly display of the fractional
# times for the new frames that will be created
def damaged_frame_fractions(damaged_frame_count : int) -> str:
    return ", ".join([f"{n + 1}/{damaged_frame_count + 1}" for n in range(damaged_frame_count)])

# For Frame Restoration, given a count of damaged frames
# compute the frame search times for the new frames that will be created
def damaged_frame_searches(damaged_frame_count : int) -> list:
    return [(n + 1.0) / (damaged_frame_count + 1.0) for n in range(damaged_frame_count)]

# For Frame Restoration, given a count of damaged frames
# and a precision (split count) compute the frames that
# are likely to be found given that precision
def damaged_frame_predictions(damaged_frame_count : int, num_splits : int) -> list:
    searches = damaged_frame_searches(damaged_frame_count)
    return [predict_search_frame(num_splits, search) for search in searches]



