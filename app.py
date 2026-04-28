from flask import Flask, render_template

from config import Config
from models.database import init_db
from routes.needs_routes import needs_bp
from routes.volunteer_routes import volunteer_bp
from routes.match_routes import match_bp

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config.from_object(Config)

init_db()

app.register_blueprint(needs_bp)
app.register_blueprint(volunteer_bp)
app.register_blueprint(match_bp)


@app.route('/')
def dashboard():
    return render_template('index.html', google_api_key=Config.GOOGLE_API_KEY)


@app.route("/submit")
def submit_page():
    return render_template("submit_need.html")


@app.route("/register")
def register_page():
    return render_template("register_volunteer.html")


if __name__ == "__main__":
    app.run(debug=True)
