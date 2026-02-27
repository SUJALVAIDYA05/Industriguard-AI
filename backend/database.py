from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    """
    Binds database to Flask app and creates
    all tables if they don't exist yet.
    """
    db.init_app(app)

    with app.app_context():
        db.create_all()
        print("[Database] Tables created / verified OK")