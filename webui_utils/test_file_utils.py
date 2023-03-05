import os
import pytest
from . import file_utils

FIXTURE_PATH = "./images"
FIXTURE_EXTENSION = "png"
FIXTURE_FILES = [os.path.join(FIXTURE_PATH, file) for file in
                 ["image0.png", "image1.png", "image2.png", "screenshot.png"]]

BAD_PATH_ARGS = [None, 1, 2.0, {3:3}, [4]]
GOOD_PATH_ARGS = [FIXTURE_PATH]
BAD_EXTENSION_ARGS = [1, 2.0, {3:3}]
GOOD_EXTENSION_ARGS = [FIXTURE_EXTENSION, None, "*", ".png", "png,gif", "png, gif", ".png,.gif",
                        ["gif", "png"], [".gif", ".png"]]
DUPLICATE_EXTENSION_ARGS = [("png", "png,png"), ("png", "png,.png"), ("*", "*,*"), ("*", "*,png")]

def test_get_files(capsys):
    # with capsys.disabled():
    #     print(os.path.abspath(FIXTURE_PATH))

    for bad_arg in BAD_PATH_ARGS:
        with pytest.raises(ValueError, match="'path' must be a string"):
            file_utils.get_files(bad_arg, FIXTURE_EXTENSION)

    for bad_arg in BAD_EXTENSION_ARGS:
        with pytest.raises(ValueError, match="'extension' must be a string, a list of strings, or 'None'"):
            file_utils.get_files(FIXTURE_PATH, bad_arg)

    # good paths should return real results
    for good_arg in GOOD_PATH_ARGS:
        result = file_utils.get_files(good_arg, FIXTURE_EXTENSION)
        assert len(result) > 0

    # excess whitespace and dots should be ignored
    for good_arg in GOOD_EXTENSION_ARGS:
        result = file_utils.get_files(FIXTURE_PATH, good_arg)
        assert len(result) > 0

    # should get a predicted set of files including the prepended path
    result = file_utils.get_files(FIXTURE_PATH, FIXTURE_EXTENSION)
    assert set(result) == set(FIXTURE_FILES)

    # should not get overlapping results
    for nondupe, dupe in DUPLICATE_EXTENSION_ARGS:
        nondupe_result = file_utils.get_files(FIXTURE_PATH, nondupe)
        dupe_result = file_utils.get_files(FIXTURE_PATH, dupe)
        assert len(dupe_result) == len(nondupe_result)
