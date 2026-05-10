from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    csrf = CSRFProtect(app)
    login_manager.login_view = 'auth.login'

    with app.app_context():
        from app import models


    from app.routes import main
    from app.auth import auth
    from app.vendor import vendor_bp
    from app.orders import orders_bp
    from app.invoices import invoices_bp
    from app.reports import reports_bp

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(vendor_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(reports_bp)


    return app