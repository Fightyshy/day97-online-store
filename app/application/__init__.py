
import os
from flask_bootstrap import Bootstrap5
from dotenv import load_dotenv
from flask import Flask, render_template
from flask_login import LoginManager
import stripe

from application.models.models import User

# Define plugins and app constants
bs5 = Bootstrap5()
login_manager = LoginManager()
login_manager.login_view = "user_auth.login"

def create_app():
    app = Flask(__name__)

    load_dotenv() # Use python_dotenv to load environmental variables from a file

    # set static path and folder to serve
    app.config["SECRET_KEY"] = os.environ["CSRF_KEY"]  # csrf
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///store.db"
    stripe.api_key = os.environ["STRIPE_API_KEY"]  # stripe test api key

    # Init app constants

    # Init plugins
    bs5.init_app(app)
    from .models.models import db
    db.init_app(app)

    # Setup flask_login
    login_manager.init_app(app)
    @login_manager.user_loader
    def load_user(user_id):
        print(user_id)
        return db.get_or_404(User, user_id)
    
    # Set error code handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", error="The requested page was not found"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("error.html", error="A error has occured on our end"), 500

    @app.errorhandler(403)
    def unauth(e):
        return render_template("error.html", "You are not authorised to access this area of the website")

    # Register blueprints
    from .views.storefront import storefront
    from .views.auth import user_auth
    from .views.product_control import product_control
    from .views.shopping_cart import shopping_cart
    from .views.user_control import user_control
    app.register_blueprint(storefront)
    app.register_blueprint(user_auth)
    app.register_blueprint(product_control)
    app.register_blueprint(shopping_cart)
    app.register_blueprint(user_control)
    return app
