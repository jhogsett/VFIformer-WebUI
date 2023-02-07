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
