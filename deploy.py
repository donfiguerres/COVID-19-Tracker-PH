""" Handles deployment of generated artifacts."""

import os
import sys
import logging
import shutil


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TRACKER_DIR = CHART_OUTPUT = os.path.join(SCRIPT_DIR, "tracker")


def deploy(source):
    dest = os.path.join(TRACKER_DIR, "charts")
    for filename in os.listdir(source):
        fullpath = os.path.join(source, filename)
        logging.info(f"Copying {filename}...")
        shutil.copy(fullpath, dest)
