from alternative_internet import app
from alternative_internet import data as db

@app.route('/')
def index():
    s = '<br/>'.join(db.get_names())
    return s