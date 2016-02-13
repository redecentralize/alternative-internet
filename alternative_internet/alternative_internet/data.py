import os
import glob
import json

from slugify import slugify

import alternative_internet.config as config

DATABASE = {}
SORTED_NAMES = []

def preload_datafiles():
    global DATABASE
    global SORTED_NAMES
    for filename in glob.glob(os.path.join(config.PROJECT_ROOT, 'projects/*.json')):
        blob = json.loads(open(filename, 'r').read())
        DATABASE[blob['name']] = blob
        SORTED_NAMES.append(blob['name'])
    SORTED_NAMES = sorted(SORTED_NAMES, key=lambda s: s.lower())

def get_names():
    return SORTED_NAMES