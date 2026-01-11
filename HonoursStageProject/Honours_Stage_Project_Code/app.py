from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "mysql+pymysql://admin:A-Strong-Password@127.0.0.1:3306/HonoursStageProject"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Example model (proves DB connection + schema)
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="user")

# Create tables once at startup
with app.app_context():
    db.create_all()

@app.route("/")
def index():
    try:
        # Simple DB check query
        db.session.execute(db.text("SELECT 1"))
        return render_template("index.html")
    except Exception as e:
        return f"Database connection failed: {e}", 500

if __name__ == "__main__":
    app.run(debug=True)