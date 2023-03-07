import os

FIXTURE_PATH = os.path.join(os.path.abspath("test_fixtures"))
FIXTURE_PATH_BAD = os.path.join(FIXTURE_PATH, "bad")
FIXTURE_PATH_ALT = os.path.join(FIXTURE_PATH, "alt")
FIXTURE_EXTENSION = "png"
FIXTURE_PNG_FILES = [os.path.join(FIXTURE_PATH, file) for file in
                 ["image0.png", "image1.png", "image2.png", "screenshot.png"]]
FIXTURE_FILES = FIXTURE_PNG_FILES + ["example.gif"]
