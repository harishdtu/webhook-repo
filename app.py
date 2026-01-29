from flask import Flask, render_template
from webhook import webhook_bp

app = Flask(__name__)

# register webhook routes
app.register_blueprint(webhook_bp)

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
