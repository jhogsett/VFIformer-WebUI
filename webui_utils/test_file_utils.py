import pytest
from . import file_utils

TEST_ASSETS_DIR = "./test_assets"
BAD_EXTENSION_ARGS = [1, 2.0, {3:3}]

def test_get_files():

    for bad_extension_arg in BAD_EXTENSION_ARGS:
        with pytest.raises(ValueError, match="'extension' must be a string, a list of strings, or 'None'"):
            file_utils.get_files(TEST_ASSETS_DIR, bad_extension_arg)
