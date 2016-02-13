from flask import render_template
from alternative_internet import app
from alternative_internet import data as db

from flaskext.markdown import Markdown
Markdown(app)

@app.route('/')
def index():
    return render_template('index.html',
            project_names=db.get_names(),
            database=db.DATABASE )