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
def float_range_in_range(target_min : float, target_max : float, domain_min : float,
                        domain_max : float, use_midpoint=False):
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
