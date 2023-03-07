import pytest # pylint: disable=import-error
from .test_defs import *
from .file_utils import get_files
from .auto_increment import *

GOOD_AIF_EXAMPLES = [
    ((FIXTURE_PATH, "*"), ("file", "txt"), (os.path.join(FIXTURE_PATH, "file5.txt"), 5)),
    ((FIXTURE_PATH, None), ("file", "txt"), (os.path.join(FIXTURE_PATH, "file5.txt"), 5)),
    ((FIXTURE_PATH, FIXTURE_EXTENSION), ("file", "txt"), (os.path.join(FIXTURE_PATH, "file4.txt"), 4)),
    ((FIXTURE_PATH, "doesnotexist"), ("file", "txt"), (os.path.join(FIXTURE_PATH, "file0.txt"), 0)),
    ((FIXTURE_PATH_ALT, FIXTURE_EXTENSION), ("file", "txt"), (os.path.join(FIXTURE_PATH_ALT, "file0.txt"), 0))]

BAD_AIF_EXAMPLES = [
    ((1, "*"), (None, None), False, "'path' must be a string"),
    ((2.0, "*"), (None, None), False, "'path' must be a string"),
    (({3:3}, "*"), (None, None), False, "'path' must be a string"),
    (([4], "*"), (None, None), False, "'path' must be a string"),
    (("", "*"), (None, None), False, "'path' must be a legal path"),
    ((".", "*"), (None, None), False, "'path' must be a legal path"),
    (("..", "*"), (None, None), False, "'path' must be a legal path"),
    (("../..", "*"), (None, None), False, "'path' must be a legal path"),
    (("test/../test", "*"), (None, None), False, "'path' must be a legal path"),
    (("..\\..", "*"), (None, None), False, "'path' must be a legal path"),
    (("test\\..\\test", "*"), (None, None), False, "'path' must be a legal path"),
    ((FIXTURE_PATH, "*"), (None, None), True, "'basename' must be a string"),
    ((FIXTURE_PATH, "*"), (1, None), True, "'basename' must be a string"),
    ((FIXTURE_PATH, "*"), (2.0, None), True, "'basename' must be a string"),
    ((FIXTURE_PATH, "*"), ({3:3}, None), True, "'basename' must be a string"),
    ((FIXTURE_PATH, "*"), ([4], None), True, "'basename' must be a string"),
    ((FIXTURE_PATH, "*"), ("", None), True, "'basename' must be a non-empty string")]

def test_AutoIncrementFlename():
    assert len(FIXTURE_FILES) == len(get_files(FIXTURE_PATH, "*"))

    for class_args, instance_args, expected in GOOD_AIF_EXAMPLES:
        assert expected == AutoIncrementFilename(*class_args).next_filename(*instance_args)

    for class_args, instance_args, test_instance, match_text in BAD_AIF_EXAMPLES:
        if not test_instance:
            # instantiating the class should raise the error
            with pytest.raises(ValueError, match=match_text):
                AutoIncrementFilename(*class_args)
        else:
            # calling the 'next' function should raise the error
            try:
                instance = AutoIncrementFilename(*class_args)
            except:
                assert False, "instantiating the class should not raise an error"
            with pytest.raises(ValueError, match=match_text):
                instance.next_filename(*instance_args)


def test_AutoIncrementDirectory():
    pass

