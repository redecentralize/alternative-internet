from alternative_internet import app

@app.route('/')
def index():
    return 'Hello World!'