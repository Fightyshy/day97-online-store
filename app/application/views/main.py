from functools import wraps
import os

from app.application.models.models import (
    Address,
    CustomerDetails,
    Order,
    ShoppingCart,
    db,
    Product,
    Comment,
    User,
    ResetTokens,
)


from app.application.objects.auth_decor import employee_check
from ..objects.forms import (
    AddressForm,
    CommentForm,
    CustomerDetailsForm,
    ProductForm,
    ProductStockForm,
    UserEditRoleForm,
    UserForm,
    UserPasswordChangeForm,
    UserRegistrationForm,
    UserPasswordResetEmailForm,
    UserPasswordResetForm,
)


from ..objects.helper_funcs import cart_merger, generate_list_id

import stripe

# sqlite db, will convert to local postgres db and dump creation script
# with app.app_context():
#     db.create_all()

# stripe api key - currently public key
# stripe.api_key = 'sk_test_51ONsITEk3v1yt26zN3nFErzHwf8JOiZuHHMljdD8n9mTNVBQp738gDd3caJSQGla0OPj7dycXVXnGkp7LxC2CSBd00A0GnUgVH'
# os.environ["STRIPE_API_KEY"]

# consts
# Temp email consts

# Fill some random countries in the area
ALLOWED = ["SG", "TH", "US", "GB", "JP", "MY", "AU"]
DEFAULT_IMAGE = "product-images/defaultimage.png" 

# error code pages
# https://flask.palletsprojects.com/en/3.0.x/errorhandling/#custom-error-pages

@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", error="The requested page was not found"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", error="A error has occured on our end"), 500

@app.errorhandler(403)
def unauth(e):
    return render_template("error.html", "You are not authorised to access this area of the website")


# product handling


# Retail store endpoints
# GET only






# shopping cart handling











# user handling endpoints





# User registration and password reset endpoints

