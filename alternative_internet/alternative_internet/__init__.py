from flask import Flask
app = Flask(__name__)

from alternative_internet.data import preload_datafiles
preload_datafiles()

import alternative_internet.views