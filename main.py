import smtplib
import jwt
import datetime as dt
from flask_login import LoginManager, current_user, login_user, logout_user
from models import (
    Address,
    CustomerDetails,
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
from helper_funcs import generate_list_id
from flask_ckeditor import CKEditor

# consts
# Temp email consts
SENDER = "testingtontester61@gmail.com"
SENDER_PASSWORD = "dyuqvhdfhrexshoa"

app = Flask(__name__)
app.config["SECRET_KEY"] = "8BYkEfBA6O6donzWlSihBXox7C0sKR6b"  # csrf
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///store.db"
Bootstrap5(app)
CKEditor(app)
db.init_app(app)

# sqlite db, will convert to local postgres db and dump creation script
with app.app_context():
    db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


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
@app.route("/products/<int:product_id>")
def show_product(product_id):
    shown_product = db.get_or_404(Product, product_id)
    comment = CommentForm()
    if comment.validate_on_submit():
        rating_val = len(comment.rating.data)
        new_comment = Comment(
            text=comment.text.data,
            rating=rating_val,
            product=show_product,
            author=current_user,
        )
        db.session.add(new_comment)
        db.session.commit()
    return render_template(
        "placeholder",
        form=comment,
        product=shown_product,
        product_id=product_id,
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


@app.route("/products/delete-product/<int:product_id>")
def delete_product(product_id):
    selected_product = db.get_or_404(Product, product_id)
    db.session.delete(selected_product)
    db.session.commit()
    return redirect(url_for("product_control_panel"))


# user handling endpoints


# TODO auth wrapper
@app.route("/user/")
def show_user_details():
    # get id, check logged in or admin
    selected_user = db.get_or_404(User, current_user.id)
    addressform = AddressForm(request.form, csrf_enabled=True)
    # render details and all addresses
    return render_template(
        "user-page.html",
        user=selected_user,
        current_user=current_user,
        form=addressform,
    )


@app.route("/edit-user/<int:user_id>")
def edit_user_details(user_id):
    # TODO get user, checked if logged in or admin
    # TODO populate form with user
    # TODO validate and submit changes to server
    return user_id


# TODO auth wrapper
@app.route("/user/add-address", methods=["POST"])
def add_address():
    print(request.form)
    addressform = AddressForm(request.form)
    print(addressform.data)
    print(addressform.validate_on_submit())
    print(addressform.errors)
    # form validate and commit to db under address
    if addressform.validate_on_submit():
        print(current_user.id)
        # Get user
        selected_user = db.get_or_404(User, current_user.id)

        # check to see if same of diff number
        phone_number = (
            selected_user.customerDetails.phone_number
            if addressform.same_number.data
            == selected_user.customerDetails.phone_number
            else addressform.phone_code.data
            + " "
            + addressform.phone_number.data
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


# TODO auth wrapper
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


@app.route("/user/delete-address/<int:address_id>")
def delete_address(address_id):
    selected_address = db.get_or_404(Address, address_id)
    db.session.delete(selected_address)
    db.session.commit()
    return redirect(url_for("show_user_details"))


@app.route("/users/control-panel", methods=["GET", "POST"])
def user_control_panel():
    # get all users
    user_list = db.session.execute(db.select(User)).scalars().all()
    roleform = UserEditRoleForm()

    return render_template("user-control.html", users=user_list, form=roleform)


@app.route("/users/delete-user/<int:user_id>")
def delete_user(user_id):
    selected_user = db.get_or_404(User, user_id)
    db.session.delete(selected_user)
    db.session.commit()
    return redirect(url_for("user_control_panel"))


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
