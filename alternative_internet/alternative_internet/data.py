import os
import glob
import json

from slugify import slugify

import alternative_internet.config as config

DATABASE = {}
SORTED_NAMES = []

def preload_datafiles():
    for filename in glob.glob(os.path.join(config.PROJECT_ROOT, 'projects/*.json')):
        blob = json.loads(open(filename, 'r').read())
        DATABASE[slugify(blob['name'])] = blob
        SORTED_NAMES.append(blob['name'])
    SORTED_NAMES.sort()

def get_names():
    return SORTED_NAMES