from functools import wraps
import smtplib
import jwt
import datetime as dt
from flask_login import LoginManager, current_user, login_user, logout_user
import pycountry
from models import (
    Address,
    CustomerDetails,
    ShoppingCart,
    db,
    Product,
    Comment,
    User,
    ResetTokens,
)
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from forms import (
    AddressForm,
    CommentForm,
    CustomerDetailsForm,
    ProductForm,
    ProductStockForm,
    UserEditRoleForm,
    UserForm,
    UserRegistrationForm,
    UserPasswordResetEmailForm,
    UserPasswordResetForm,
)
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash
from flask_bootstrap import Bootstrap5
from helper_funcs import cart_merger, generate_list_id
from sqlalchemy import and_
import stripe

# set static path and folder to serve
app = Flask(__name__, static_url_path="", static_folder="assets")
app.config["SECRET_KEY"] = "8BYkEfBA6O6donzWlSihBXox7C0sKR6b"  # csrf
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///store.db"

Bootstrap5(app)
db.init_app(app)

# sqlite db, will convert to local postgres db and dump creation script
with app.app_context():
    db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)

# stripe api key
stripe.api_key = "sk_test_Ou1w6LVt3zmVipDVJsvMeQsc"

# consts
# Temp email consts
SENDER = "testingtontester61@gmail.com"
SENDER_PASSWORD = "dyuqvhdfhrexshoa"
# Fill some random countries in the area
ALLOWED = ["SG", "TH", "US", "GB", "JP", "MY", "AU"]


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


# auth decorators
def logged_in_check(f):
    """Checks if a user is logged in, renders error page with a 403 error if not"""

    @wraps(f)
    def dec_func(*args, **kwargs):
        if current_user.is_authenticated():
            return f(*args, **kwargs)
        else:
            return render_template("error.html", status=403)

    return dec_func


def employee_check(f):
    """Checks if the current user is a admin or employee, renders error page with a 403 error if not"""

    @wraps(f)
    def dec_func(*args, **kwargs):
        if current_user.is_authenticated() and (
            current_user.role == "admin" or "employee"
        ):
            return f(*args, **kwargs)
        else:
            return render_template("error.html", status=403)

    return dec_func


def admin_check(f):
    """Checks if current user is a admin, renders error page with a 403 error if not"""

    @wraps(f)
    def dec_func(*args, **kwargs):
        if current_user.is_authenticated() and (current_user.role == "admin"):
            return f(*args, **kwargs)
        else:
            return render_template("error.html", status=403)

    return dec_func


# product handling
@app.route("/")
def home():
    # join with comments to access comment.rating
    # group by product to consolidate dupes from children
    # having to filter based on product rating avg by threshold
    featured_products = (
        db.session.execute(
            db.select(Product)
            .join(Product.comments)
            .group_by(Product)
            .having(func.avg(Comment.rating) >= 4)
        )
        .scalars()
        .all()
    )

    # print([value.comments.rating for value in featured_products])
    return render_template("index.html", featured=featured_products)


# Retail store endpoints
# GET only
@app.route("/products/<int:product_id>", methods=["GET", "POST"])
def show_product(product_id):
    shown_product = db.get_or_404(Product, product_id)
    commentform = CommentForm()
    if commentform.validate_on_submit():
        selected_user = db.get_or_404(User, current_user.id)
        rating_val = len(commentform.rating.data)
        new_comment = Comment(
            comment=commentform.comment.data,
            rating=rating_val,
            product=shown_product,
            customer=selected_user.customerDetails,
        )
        db.session.add(new_comment)
        db.session.commit()
    return render_template(
        "product-detail.html",
        form=commentform,
        product=shown_product,
        product_id=product_id,
    )


@employee_check
@app.route("/products/delete-comment/<int:comment_id>")
def delete_comment(comment_id):
    selected_comment = db.get_or_404(Comment, comment_id)
    db.session.delete(selected_comment)
    db.session.commit()
    return redirect(
        url_for("show_product", product_id=selected_comment.product_id)
    )


@app.route("/products/control-panel", methods=["GET", "POST"])
def product_control_panel():
    product_list = db.session.execute(db.select(Product)).scalars().all()
    productform = ProductForm()

    # if request.method=="POST":
    if productform.validate_on_submit():
        product_uid = generate_list_id()
        while True:
            if (
                db.session.execute(
                    db.select(Product).where(
                        Product.product_uid == product_uid
                    )
                ).scalar()
                is not None
            ):
                product_uid = generate_list_id()
            else:
                break
        set_image = (
            "assets/images/defaultimage.jpg"
            if productform.image.data == ""
            else f"assets/images/{productform.image.data}"
        )
        new_product = Product(
            name=productform.name.data,
            product_uid=product_uid,
            description=productform.description.data,
            price=productform.price.data,
            stock=productform.stock.data,
            image=set_image,
            category=productform.category.data,
        )
        db.session.add(new_product)
        db.session.commit()
        return redirect(url_for("product_control_panel"))

    return render_template(
        "product-control.html", products=product_list, form=productform
    )


@employee_check
@app.route("/products/edit-stock/<int:product_id>", methods=["GET", "POST"])
def edit_product_stock(product_id):
    selected_product = db.get_or_404(Product, product_id)
    if request.method == "POST":
        stockform = ProductStockForm(request.form)
        if stockform.validate():
            selected_product.stock = stockform.stock.data
            db.session.commit()
            return jsonify({"product": {"stock": selected_product.stock}})
    return jsonify({"product": {"stock": selected_product.stock}})


@employee_check
@app.route("/products/edit-product/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    # get product from db
    selected_product = db.get_or_404(Product, product_id)
    # recieve post request
    if request.method == "POST":
        productform = ProductForm(request.form)
        if productform.validate():
            if productform.image.data is None:
                set_image = f"assets/images/{productform.image.data}"
                selected_product.image = set_image
            else:
                selected_product.image = productform.image.data
            # edit product from db contents with request
            selected_product.name = productform.name.data
            selected_product.description = productform.description.data
            selected_product.price = productform.price.data
            selected_product.stock = productform.stock.data
            selected_product.category = productform.category.data
            # commit changes
            db.session.commit()
            return ""
        else:
            return jsonify({"status": "not-found"})
    payload = jsonify(
        {
            "status": "ok",
            "product": {
                "name": selected_product.name,
                "description": selected_product.description,
                "price": selected_product.price,
                "stock": selected_product.stock,
                "category": selected_product.category,
                "image": selected_product.image,
            },
        }
    )
    return payload


@admin_check
@app.route("/products/delete-product/<int:product_id>")
def delete_product(product_id):
    selected_product = db.get_or_404(Product, product_id)
    db.session.delete(selected_product)
    db.session.commit()
    return redirect(url_for("product_control_panel"))


# shopping cart handling


@logged_in_check
@app.route("/shopping-cart")
def show_shopping_cart():
    selected_user_cart = db.get_or_404(
        User, current_user.id
    ).customerDetails.shoppingcart
    uids = [id.product_uid for id in selected_user_cart]
    products_in_cart = (
        db.session.execute(
            # in_ allows us to get from list of product_uids
            db.select(Product).where(Product.product_uid.in_(uids))
        )
        .scalars()
        .all()
    )

    truecart = []
    for item in selected_user_cart:
        for product in products_in_cart:
            if item.product_uid == product.product_uid:
                truecart.append({"cartobj": item, "productref": product})

    # initial subtotal
    init_subtotal = "{0:.2f}".format(
        sum(
            [
                float(item["cartobj"].quantity * item["productref"].price)
                for item in truecart
            ]
        )
    )
    return render_template(
        "shopping-cart.html",
        cart=truecart,
        current_user=current_user,
        subtotal=init_subtotal,
    )


@app.route("/cart/checkout", methods=["GET", "POST"])
def show_checkout():
    truecart = cart_merger(db, current_user)
    final_total = "{0:.2f}".format(
        sum(
            [
                float(item["cartobj"].quantity * item["productref"].price)
                for item in truecart
            ]
        )
        + 10  # shipping cost (flat fee)
    )
    return render_template("checkout.html", total=final_total, cart=truecart)


# stripe will call this to generate it's own embed
@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    try:
        truecart = cart_merger(db, current_user)
        list_stripe_products = [
            stripe.Product.create(
                name=item["productref"].name,
                description=item["productref"].description,
                unit_label=item["cartobj"].product_uid,
            )
            for item in truecart
        ]

        list_stripe_cart = []
        for i in range(0, len(list_stripe_products)):
            list_stripe_cart.append(
                {
                    "price": stripe.Price.create(
                        product=list_stripe_products[i],
                        unit_amount=int(
                            truecart[i]["productref"].price * 100
                        ),  # To cents x100 and cast int
                        currency="usd",
                    ),
                    "quantity": truecart[i]["cartobj"].quantity,
                }
            )

        session = stripe.checkout.Session.create(
            ui_mode="embedded",
            line_items=[
                {"price": item["price"].id, "quantity": item["quantity"]}
                for item in list_stripe_cart
            ],
            mode="payment",
            invoice_creation={"enabled" : True},
            shipping_address_collection={"allowed_countries": ALLOWED},
            # generate options on session create, extend more as necessary
            shipping_options=[
                {
                    "shipping_rate_data": {
                        "type": "fixed_amount",
                        "fixed_amount": {"amount": 1000, "currency": "usd"},
                        "display_name": "Flat rate shipping",
                        "delivery_estimate": {
                            "minimum": {"unit": "business_day", "value": 5},
                            "maximum": {"unit": "business_day", "value": 7},
                        },
                    },
                }
            ],
            return_url="http://localhost:5000/checkout-success",
        )
    except Exception as e:
        return str(e)

    return jsonify(clientSecret=session.client_secret)


@logged_in_check
@app.route("/checkout-success")
def successful_payment():
    # get cart first for invoicing
    # clean shopping cart of user
    selected_user = db.get_or_404(User, current_user.id)
    # https://stackoverflow.com/questions/48839482/deleting-list-of-items-in-sqlalchemy-flask
    ShoppingCart.query.filter(
        ShoppingCart.customer.has(
            CustomerDetails.id == selected_user.customerDetails.id
        )
    ).delete()

    db.session.commit()
    return render_template("successful_checkout.html")


@logged_in_check
@app.route("/cart/add-to-cart", methods=["POST"])
def add_to_cart():
    if request.method == "POST":
        # for directly retrieving json
        # https://stackoverflow.com/questions/10434599/get-the-data-received-in-a-flask-request
        get_user = db.get_or_404(User, current_user.id)
        check_exist = db.session.execute(
            db.select(ShoppingCart)
            .where(ShoppingCart.customer_id == get_user.customerDetails.id)
            .where(ShoppingCart.product_uid == request.json["product_uid"])
        ).scalar()
        if check_exist is None:
            new_item = ShoppingCart(
                product_uid=request.json["product_uid"],
                quantity=request.json["quantity"],
                customer=get_user.customerDetails,
            )
            db.session.add(new_item)
            db.session.commit()
            return ""
        else:
            check_exist.quantity += int(request.json["quantity"])
            db.session.commit()
            return ""
    return ""


@logged_in_check
@app.route("/cart/remove-from-cart/<int:cart_id>", methods=["POST"])
def remove_from_cart(cart_id):
    if request.method == "POST":
        selected_cart_item = db.get_or_404(ShoppingCart, cart_id)
        db.session.delete(selected_cart_item)
        db.session.commit()
        return ""


@logged_in_check
@app.route("/cart/change-quantity", methods=["POST"])
def change_product_quantity():
    if request.method == "POST":
        selected_cart_item = db.get_or_404(
            ShoppingCart, request.json["cart_id"]
        )
        selected_cart_item.quantity = request.json["quantity"]
        db.session.commit()
        return jsonify({"new_quantity": selected_cart_item.quantity})


# user handling endpoints


@logged_in_check
@app.route("/user")
def show_user_details():
    # get id, check logged in or admin
    selected_user = db.get_or_404(User, current_user.id)
    addressform = AddressForm(request.form, csrf_enabled=True)
    customerdetailsform = CustomerDetailsForm(csrf_enabled=True)
    # render details and all addresses
    return render_template(
        "user-page.html",
        user=selected_user,
        current_user=current_user,
        form=addressform,
        detailform=customerdetailsform,
    )


@logged_in_check
@app.route("/edit-user", methods=["GET", "POST"])
def edit_user_details():
    # get user, checked if logged in or admin
    selected_user = db.get_or_404(User, current_user.id)
    if request.method == "POST":
        # validate and submit changes to server
        customerdetailsform = CustomerDetailsForm(request.form)
        if customerdetailsform.validate():
            selected_user.customerDetails.first_name = (
                customerdetailsform.first_name.data
            )
            selected_user.customerDetails.last_name = (
                customerdetailsform.last_name.data
            )
            selected_user.customerDetails.date_of_birth = (
                customerdetailsform.date_of_birth.data
            )
            phone_number = f"{customerdetailsform.phone_code.data} {customerdetailsform.phone_number.data}"
            selected_user.customerDetails.phone_number = phone_number
            db.session.commit()
            return ""
    if selected_user.role == "user":
        (
            phone_code,
            phone_number,
        ) = selected_user.customerDetails.phone_number.split(" ")
        # populate form with user
        return jsonify(
            {
                "customerDetails": {
                    "first_name": selected_user.customerDetails.first_name,
                    "last_name": selected_user.customerDetails.last_name,
                    "dob": selected_user.customerDetails.date_of_birth.strftime(
                        "%Y-%m-%d"
                    ),
                    "phone_code": phone_code,
                    "phone_number": phone_number,
                }
            }
        )


@logged_in_check
@app.route("/user/add-address", methods=["POST"])
def add_address():
    addressform = AddressForm(request.form)
    print(addressform.validate_on_submit())
    # form validate and commit to db under address
    if addressform.validate_on_submit():
        print(current_user.id)
        # Get user
        selected_user = db.get_or_404(User, current_user.id)

        # check to see if same of diff number
        phone_number = (
            selected_user.customerDetails.phone_number
            if addressform.same_number.data is True
            else f"{addressform.phone_code} {addressform.phone_number}"
        )

        # Make new address obj
        new_address = Address(
            address_one=addressform.address_one.data,
            address_two=addressform.address_two.data,
            state=addressform.state.data,
            city=addressform.city.data,
            postcode=addressform.postal_code.data,
            country=addressform.country.data,
            phone_number=phone_number,
            customer=selected_user.customerDetails,
        )
        # Update customerDetails address with address
        selected_user.customerDetails.addresses.append(new_address)
        db.session.commit()
        return ""
    return "form for adding new address"


@logged_in_check
@app.route("/user/edit-address/<int:address_id>", methods=["GET", "POST"])
def edit_address(address_id):
    # get address from address id, check if user id matches logged in user
    selected_user = db.get_or_404(User, current_user.id)
    selected_address = db.get_or_404(Address, address_id)
    # TODO update with data from form
    if request.method == "POST":
        addressform = AddressForm(request.form)
        if addressform.validate():
            selected_address.address_one = addressform.address_one.data
            selected_address.address_two = addressform.address_two.data
            selected_address.state = addressform.state.data
            selected_address.city = addressform.city.data
            selected_address.postcode = addressform.postal_code.data
            selected_address.country = addressform.country.data
            selected_address.phone_number = f"{addressform.phone_code.data} {addressform.phone_number.data}"
            db.session.commit()
            return ""

    if selected_address in selected_user.customerDetails.addresses:
        phone_code, phone_number = selected_address.phone_number.split(" ")
        print(phone_code + "lol" + phone_number)
        return jsonify(
            {
                "address": {
                    "address_one": selected_address.address_one,
                    "address_two": selected_address.address_two,
                    "state": selected_address.state,
                    "city": selected_address.city,
                    "postal_code": selected_address.postcode,
                    "country": selected_address.country,
                    "phone_code": phone_code,
                    "phone_number": phone_number,
                }
            }
        )


@logged_in_check
@app.route("/user/delete-address/<int:address_id>")
def delete_address(address_id):
    selected_address = db.get_or_404(Address, address_id)
    db.session.delete(selected_address)
    db.session.commit()
    return redirect(url_for("show_user_details"))


# admin/employee control panel handling


@employee_check
@app.route("/users/control-panel", methods=["GET", "POST"])
def user_control_panel():
    # get all users
    user_list = db.session.execute(db.select(User)).scalars().all()
    roleform = UserEditRoleForm()

    return render_template("user-control.html", users=user_list, form=roleform)


@admin_check
@app.route("/users/delete-user/<int:user_id>")
def delete_user(user_id):
    selected_user = db.get_or_404(User, user_id)
    db.session.delete(selected_user)
    db.session.commit()
    return redirect(url_for("user_control_panel"))


@admin_check
@app.route("/users/edit-role/<int:user_id>", methods=["POST"])
def edit_role(user_id):
    # handle AJAX
    if request.method == "POST":
        # recieve field inputs
        new_role = request.form.get("role")
        # select user and update user fields and commit
        selected_user = db.get_or_404(User, user_id)
        selected_user.role = new_role
        db.session.commit()
        return jsonify({"role": selected_user.role})
    # AJAX no redirect/render
    return ""


# User registration and password reset endpoints


@app.route("/users/login", methods=["GET", "POST"])
def login():
    loginform = UserForm()
    if loginform.validate_on_submit():
        result = db.session.execute(
            db.select(User).where(User.email == loginform.email.data)
        )
        user = result.scalar()
        if not user:
            flash("User does not exist, please make a new account")
            return redirect(url_for("login"))
        if not check_password_hash(user.password, loginform.password.data):
            flash("Wrong password")
            return redirect(url_for("login"))
        else:
            login_user(user)
            return redirect(url_for("home"))
    return render_template(
        "login.html", form=loginform, current_user=current_user
    )


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/users/register", methods=["GET", "POST"])
def register():
    # usage of csrf_enabled https://stackoverflow.com/questions/38231010/generating-a-csrf-token-manually-with-flask-wtf-forms
    registerform = UserRegistrationForm(csrf_enabled=True)
    if registerform.validate_on_submit():
        if registerform.password.data == registerform.repeat_password.data:
            if (
                db.session.execute(
                    db.select(User).where(
                        User.email == registerform.email.data
                    )
                ).scalar()
                is not None
            ):
                flash("User email already exists, login using it")
                return redirect((url_for("login")))

            hashed_pw = generate_password_hash(registerform.password.data)
            new_details = CustomerDetails(
                first_name=registerform.details.first_name.data,
                last_name=registerform.details.last_name.data,
                date_of_birth=registerform.details.date_of_birth.data,
                phone_number=f"{registerform.details.phone_code.data} {registerform.details.phone_number.data}",
            )
            new_user = User(
                username=registerform.username.data,
                email=registerform.email.data,
                password=hashed_pw,
                role="user",
                customerDetails=new_details,
            )
            db.session.add(new_details)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for("home"))
        else:
            print("don't be here")
            flash("Passwords do not match")
            return redirect(url_for("home"))

    return render_template(
        "register.html", form=registerform, current_user=current_user
    )


@app.route("/users/reset-password", methods=["GET", "POST"])
def reset_password():
    emailform = UserPasswordResetEmailForm()
    if emailform.validate_on_submit():
        selected_user = db.session.execute(
            db.select(User).where(User.email == emailform.email.data)
        ).scalar()
        print(selected_user)
        # create jwt payload
        reset = {
            "username": selected_user.username,
            "email": selected_user.email,
            # expire +6 hours from generation
            "exp": dt.datetime.now() + dt.timedelta(hours=6),
        }
        # encode to jwt with hs256 and secret
        token_secret = selected_user.username + selected_user.email
        token = jwt.encode(reset, token_secret, algorithm="HS256")

        # add to pass reset db with email and username
        trunc_hash = ResetTokens(
            username=selected_user.username,
            email=selected_user.email,
            token=token,
        )
        db.session.add(trunc_hash)
        db.session.commit()

        # smtp send link+reset-token param and hash
        with smtplib.SMTP("smtp.gmail.com", port=587) as mailer:
            message = f"""We've recieved a password reset request for your account
                        Here's the link http://localhost:5000{url_for("validate_reset", reset_token=trunc_hash.token)}
                        If you did not request this password reset to your account please ignore this email."""
            mailer.starttls()
            mailer.login(user=SENDER, password=SENDER_PASSWORD)
            mailer.sendmail(
                to_addrs=selected_user.email,
                from_addr="test@test.com",
                msg=f"Subject:Store user password reset\n\n{message}",
            )
        return render_template("confirm-reset.html")

    return render_template("reset-password.html", form=emailform)


@app.route("/users/validate-reset", methods=["GET", "POST"])
def validate_reset():
    resetform = UserPasswordResetForm()
    try:
        # try to get request token
        token = request.args.get("reset_token")
    except KeyError:
        # flash link invalidity and redirect to reset screen
        flash("The reset link is invalid.")
        return redirect(url_for("reset_password"))
    else:
        if resetform.validate_on_submit():
            # reacquire token
            token = resetform.token.data
            # try to decode token
            selected_token = db.session.execute(
                db.select(ResetTokens).where(ResetTokens.token == token)
            ).scalar()
            decoded_token = jwt.decode(
                token,
                selected_token.username + selected_token.email,
                ["HS256"],
            )
            # check if token is expired and flash if it is
            if (
                dt.datetime.fromtimestamp(decoded_token["exp"]).date()
                < dt.datetime.now().date()
            ):
                flash("This password token has expired.")
                return redirect(url_for("reset_password"))
            # elif resetform.password.data != resetform.repeat.data:
            #     flash("The passwords do not match, please try again.")
            #     return redirect(url_for("validate_reset", token=token))
            # Retrieve user with email
            selected_user = db.session.execute(
                db.select(User).where(User.email == decoded_token["email"])
            ).scalar()
            # Change password and update db
            selected_user.password = generate_password_hash(
                resetform.password.data
            )
            db.session.delete(selected_token)
            db.session.commit()

            # Render success page
            return render_template("successful-reset.html")
        return render_template(
            "new-password.html", form=resetform, token=token
        )

    # TODO validate dual password input


if __name__ == "__main__":
    app.run(debug=True)
