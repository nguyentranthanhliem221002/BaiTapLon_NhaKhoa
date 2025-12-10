from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.model import Model

app = Flask(__name__)

# ==============================
# CẤU HÌNH DATABASE
DB_USER = "root"
DB_PASSWORD = ""
DB_HOST = "localhost"
DB_NAME = "nha_khoa"
DB_CHARSET = "utf8mb4"

Base = Model

SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?charset={DB_CHARSET}"
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["PAGE_SIZE"] = 2
app.secret_key = "supersecretkey"

data = SQLAlchemy(app)