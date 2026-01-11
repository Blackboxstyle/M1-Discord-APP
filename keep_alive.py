from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "✨ M1 está viva y cuidando el clan T.F.G! 🖤"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()