import smtplib
import jwt
import datetime as dt
from flask_login import LoginManager, current_user, login_user
from models import db, Product, Comment, User, ResetTokens
from flask import Flask, flash, redirect, render_template, request, url_for
from forms import (
    CommentForm,
    UserForm,
    UserRegistrationForm,
    UserPasswordResetEmailForm,
    UserPasswordResetForm,
)
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash
from flask_bootstrap import Bootstrap5

# consts
# Temp email consts
SENDER = "testingtontester61@gmail.com"
SENDER_PASSWORD = "dyuqvhdfhrexshoa"

app = Flask(__name__)
app.config["SECRET_KEY"] = "8BYkEfBA6O6donzWlSihBXox7C0sKR6b" #csrf
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///store.db"
Bootstrap5(app)
db.init_app(app)

# sqlite db, will convert to local postgres db and dump creation script
# with app.app_context():
#     db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


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


@app.route("/user/<int:user_id>")
def show_user_details(user_id):
    # TODO get id, check logged in or admin
    # TODO render details and all addresses
    return user_id


@app.route("/edit-user/<int:user_id>")
def edit_user_details(user_id):
    # TODO get user, checked if logged in or admin
    # TODO populate form with user
    # TODO validate and submit changes to server
    return user_id


@app.route("/user/<int:user_id>/add-address")
def add_address(user_id):
    # TODO form validate and commit to db under address
    return "form for adding new address"


@app.route("/user/<int:user_id>/<int:address_id>")
def edit_address(user_id, address_id):
    # TODO get address from address id, check if user id matches logged in user
    # TODO update with data from form
    return "Populated form for address"


# user handling endpoints
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
            return redirect(url_for("main_page"))
    return render_template(
        "login.html", form=loginform, current_user=current_user
    )


@app.route("/users/register", methods=["GET", "POST"])
def register():
    registerform = UserRegistrationForm()
    if registerform.validate_on_submit():
        if db.session.execute(
            db.select(User).where(User.email == registerform.email.data)
        ):
            flash("User email already exists, login using it")
            return redirect((url_for("login")))
        if registerform.password.data == registerform.repeat_pw.data:
            hashed_pw = generate_password_hash(registerform.password.data)
            new_user = User(
                username=registerform.username.data,
                email=registerform.email.data,
                password=hashed_pw,
                role="user",
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for("main_page"))
        else:
            pass
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
        # create jwt payload
        reset = {
            "username": selected_user.username,
            "email": selected_user.email,
            # expire +6 hours from generation
            "exp": dt.datetime.now()+dt.timedelta(hours=6)
        }
        # encode to jwt with hs256 and secret
        token_secret = selected_user.username+selected_user.email
        token = jwt.encode(reset, token_secret, algorithm=["HS256"])

        # add to pass reset db with email and username
        trunc_hash = ResetTokens(
            username=selected_user.username.data,
            email=selected_user.email.data,
            token=token
        )
        db.session.add(trunc_hash)
        db.session.commit()

        # TODO smtp send link+reset-token param and hash
        with smtplib.SMTP("smtp.gmail.com", port=587) as mailer:
            message = f"""We've recieved a password reset request for your
                            account\n
                            Here's the link {url_for("validate_reset", reset_token=hash)}\n\n
                        If you did not request this password reset to your
                        account
                        please ignore this email."""
            mailer.starttls()
            mailer.login(user=SENDER, password=SENDER_PASSWORD)
            mailer.sendmail(
                to_addrs=selected_user.email,
                from_addr="test@test.com",
                msg=f"Subject:Store user password reset\n\n{message}",
            )
        # TODO render confirm reset page
        return render_template("confirm_reset.html")

    return render_template("reset-password.html", form=emailform)


@app.route("/users/validate-reset")
def validate_reset():
    try:
        token = request.args.get("reset_token")
    except KeyError:
        # TODO show invalid link error
        pass
    else:
        # TODO reconstruct hash

        # 
        resetform = UserPasswordResetForm()
        pass

    # TODO request.args.reset-token param
    # TODO select from pass reset db and get email+username
    # TODO select from user db with email+username
    # TODO validate dual password input
    # TODO hash password
    # TODO update selected user with new password
    # TODO render success page
    return render_template("successful-reset.html")


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


if __name__ == "__main__":
    app.run(debug=True)
