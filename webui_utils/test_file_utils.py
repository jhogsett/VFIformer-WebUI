import os
import pytest # pylint: disable=import-error
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

GOOD_PATH_SPLITS = [
    ("path1/path2/filename.extension", ("path1/path2", "filename", ".extension")),
    ("/filename.extension", ("/", "filename", ".extension")),
    ("/filename", ("/", "filename", "")),
    ("filename", ("", "filename", "")),
    (".filename", ("", ".filename", "")),
    (".", ("", ".", "")),
    ("", ("", "", ""))]

BAD_PATH_SPLITS = [
    (None, (None, None, None)),
    (1, (None, None, None)),
    (2.0, (None, None, None)),
    ({3:3}, (None, None, None)),
    ([4], (None, None, None))]

def test_split_filepath():
    for split_str, split_list in BAD_PATH_SPLITS:
        with pytest.raises(ValueError, match="'filepath' must be a string"):
            file_utils.split_filepath(split_str) == split_list

    for split_str, split_list in GOOD_PATH_SPLITS:
        assert file_utils.split_filepath(split_str) == split_list

GOOD_BUILD_FILENAME_ARGS = [
    (("filename1.ext", None, None), "filename1.ext"),
    (("filename2.ext", "", ""), ""),
    ((None, "somefile1", "txt"), "somefile1.txt"),
    (("", "somefile2", "txt"), "somefile2.txt"),
    ((None, None, None), ""),
    (("", "", ""), ""),
    (("filename1.ext", None, ".txt"), "filename1.txt"),
    (("filename2.ext", None, "txt"), "filename2.txt"),
    (("filename.ext", "somefile3", None), "somefile3.ext"),
    (("filename4.ext", "", ".txt"), ".txt"),
    (("filename5.ext", "", "txt"), ".txt"),
    (("filename.ext", "somefile4", ""), "somefile4"),
    (("filename.ext", "somefile5", "txt"), "somefile5.txt"),
    (("filename.ext", None, ""), "filename"),
    (("filename.ext", "", None), ".ext")]

BAD_BUILD_FILENAME_ARGS = [
    ((1, 1, 1), "'base_file_ext' must be a string or None"),
    ((2.0, 2.0, 2.0), "'base_file_ext' must be a string or None"),
    (({3:3}, {3:3}, {3:3}), "'base_file_ext' must be a string or None"),
    (([4], [4], [4]), "'base_file_ext' must be a string or None"),
    (("", 1, 1), "'file_part' must be a string or None"),
    (("", 2.0, 2.0), "'file_part' must be a string or None"),
    (("", {3:3}, {3:3}), "'file_part' must be a string or None"),
    (("", [4], [4]), "'file_part' must be a string or None"),
    ((None, 1, 1), "'file_part' must be a string or None"),
    ((None, 2.0, 2.0), "'file_part' must be a string or None"),
    ((None, {3:3}, {3:3}), "'file_part' must be a string or None"),
    ((None, [4], [4]), "'file_part' must be a string or None"),
    (("", "", 1), "'ext_part' must be a string or None"),
    (("", "", 2.0), "'ext_part' must be a string or None"),
    (("", "", {3:3}), "'ext_part' must be a string or None"),
    (("", "", [4]), "'ext_part' must be a string or None"),
    ((None, None, 1), "'ext_part' must be a string or None"),
    ((None, None, 2.0), "'ext_part' must be a string or None"),
    ((None, None, {3:3}), "'ext_part' must be a string or None"),
    ((None, None, [4]), "'ext_part' must be a string or None")]

def test_build_filename():
    for good_args, result in GOOD_BUILD_FILENAME_ARGS:
        assert result == file_utils.build_filename(*good_args)

    for bad_args, match_text in BAD_BUILD_FILENAME_ARGS:
        with pytest.raises(ValueError, match=match_text):
            file_utils.build_filename(*bad_args)

GOOD_BUILD_INDEXED_FILENAME_ARGS = [
    (("filename1", "ext", 1, 100), "filename1001.ext"),
    (("filename2.ext", None, 1, 100), "filename2001.ext"),
    (("filename3", "ext", 12345, 99999), "filename312345.ext"),
    (("filename4", "ext", 0, 100), "filename4000.ext"),
    (("", "ext", 1, 100), "001.ext"),
    (("filename5", None, 1, 100), "filename5001"),
    (("filename6", "", 1, 100), "filename6001")]

BAD_BUILD_INDEXED_FILENAME_ARGS = [
    ((None, "ext", 1, 100), "'filename' must be a string"),
    ((1, "ext", 1, 100), "'filename' must be a string"),
    ((2.0, "ext", 1, 100), "'filename' must be a string"),
    (({3:3}, "ext", 1, 100), "'filename' must be a string"),
    (([4], "ext", 1, 100), "'filename' must be a string"),
    (("", 1, 1, 100), "'extension' must be a string"),
    (("", 2.0, 1, 100), "'extension' must be a string"),
    (("", {3:3}, 1, 100), "'extension' must be a string"),
    (("", [4], 1, 100), "'extension' must be a string"),
    (("", "", None, 100), "'index' must be an int or float"),
    (("", "", "", 100), "'index' must be an int or float"),
    (("", "", {3:3}, 100), "'index' must be an int or float"),
    (("", "", [4], 100), "'index' must be an int or float"),
    (("", "", 0, None), "'max_index' must be an int or float"),
    (("", "", 0, ""), "'max_index' must be an int or float"),
    (("", "", 0, {3:3}), "'max_index' must be an int or float"),
    (("", "", 0, [4]), "'max_index' must be an int or float"),
    (("", "", -1, 100), "'index' value must be >= 0"),
    (("", "", -2.0, 100), "'index' value must be >= 0"),
    (("", "", 0, -1), "'max_index' value must be >= 1"),
    (("", "", 0, -2.0), "'max_index' value must be >= 1"),
    (("", "", 100, 90), "'max_index' value must be >= 'index'")]

def test_build_indexed_filename():
    for good_args, result in GOOD_BUILD_INDEXED_FILENAME_ARGS:
        assert result == file_utils.build_indexed_filename(*good_args)

    for bad_args, match_text in BAD_BUILD_INDEXED_FILENAME_ARGS:
        with pytest.raises(ValueError, match=match_text):
            file_utils.build_indexed_filename(*bad_args)

GOOD_BUILD_SERIES_FILENAME_ARGS = [
    (("pngsequence", "png", 1, 10, None), "pngsequence01.png"),
    (("pngsequence", ".png", 2, 100, None), "pngsequence002.png"),
    (("pngsequence", "gif", 10, 1000, "somefile.txt"), "pngsequence0010.gif"),
    (("pngsequence00", "png", 1, 10, None), "pngsequence0001.png"),
    (("pngsequence", None, 1, 9, "somefile.txt"), "pngsequence1.txt"),
    ((None, "jpg", 0, 9, "somefile.txt"), "somefile.jpg"),
    ((None, None, 0, 1, "somefile.txt"), "somefile.txt"),
    (("pngsequence", "png", 2.0, 10, None), "pngsequence02.png"),
    (("pngsequence", "png", 3, 333.0, None), "pngsequence003.png"),
    (("pngsequence", "png", 4.0, 4444.0, None), "pngsequence0004.png"),
    ((None, None, 0, 1, "somefile"), "somefile"),
    ((None, "png", 0, 1, "somefile"), "somefile.png"),
    ((None, None, 0, 1, ".ext"), ".ext"),
    ((None, None, 0, 1, ""), ""),
    ((None, None, 0, 1, None), ""),
    (("somefile", None, 0, 1, ".ext"), "somefile0"),
    (("somefile", None, 0, 1, "other.ext"), "somefile0.ext"),
    ((None, None, 0, 0, None), ""),
]

BAD_BUILD_SERIES_FILENAME_ARGS = [
    (("pngsequence", None, 0, 0, None), "'max_index' value must be >= 1"),
    (("pngsequence", None, -1, 0, None), "'index' value must be >= 0"),
    (("pngsequence", None, 0, -1, None), "'max_index' value must be >= 1"),
    (("pngsequence", None, 2, 1, None), "'max_index' value must be >= 'index'"),
    ((1, None, 0, 0, None), "'filename' must be a string"),
    ((2.0, None, 0, 0, None), "'filename' must be a string"),
    (({3:3}, None, 0, 0, None), "'filename' must be a string"),
    (([4], None, 0, 0, None), "'filename' must be a string"),
    (("", 1, 0, 0, None), "'ext_part' must be a string or None"),
    (("", 2.0, 0, 0, None), "'ext_part' must be a string or None"),
    (("", {3:3}, 0, 0, None), "'ext_part' must be a string or None"),
    (("", [4], 0, 0, None), "'ext_part' must be a string or None"),
    (("", "", 0, 0, 1), "'base_file_ext' must be a string or None"),
    (("", "", 0, 0, 2.0), "'base_file_ext' must be a string or None"),
    (("", "", 0, 0, {3:3}), "'base_file_ext' must be a string or None"),
    (("", "", 0, 0, [4]), "'base_file_ext' must be a string or None"),
]

def test_build_series_filename():
    for good_args, result in GOOD_BUILD_SERIES_FILENAME_ARGS:
        assert result == file_utils.build_series_filename(*good_args)

    for bad_args, match_text in BAD_BUILD_SERIES_FILENAME_ARGS:
        with pytest.raises(ValueError, match=match_text):
            file_utils.build_series_filename(*bad_args)
