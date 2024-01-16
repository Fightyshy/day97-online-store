import os
from flask import Blueprint, render_template
from flask_login import current_user, login_required, login_user, logout_user
from flask import (
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from werkzeug.security import generate_password_hash, check_password_hash
import phonenumbers
import datetime as dt
import smtplib
import jwt

from ..objects.forms import UserForm, UserPasswordChangeForm, UserPasswordResetEmailForm, UserPasswordResetForm, UserRegistrationForm
from ..models.models import CustomerDetails, ResetTokens, User, db

# Declare here instead because we've already loaded .env in init
SENDER = os.environ["EMAIL"]
SENDER_PASSWORD = os.environ["EMAIL_PASSWORD"]

user_auth = Blueprint("user_auth", __name__, template_folder="templates")

@user_auth.route("/users/login", methods=["GET", "POST"])
def login():
    loginform = UserForm()
    if loginform.validate_on_submit():
        result = db.session.execute(
            db.select(User).where(User.email == loginform.email.data)
        )
        user = result.scalar()
        if not user:
            flash("User does not exist, please make a new account")
            return redirect(url_for("user_auth.login"))
        if not check_password_hash(user.password, loginform.password.data):
            flash("Wrong password")
            return redirect(url_for("user_auth.login"))
        else:
            login_user(user)
            return redirect(url_for("storefront.home"))
    return render_template(
        "login.html", form=loginform, current_user=current_user
    )


@user_auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("storefront.home"))


@user_auth.route("/users/register", methods=["GET", "POST"])
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
                return redirect((url_for("user_auth.login")))

            hashed_pw = generate_password_hash(registerform.password.data)
            parsed_number = phonenumbers.parse(
                registerform.details.phone_number.data
            )
            new_details = CustomerDetails(
                first_name=registerform.details.first_name.data,
                last_name=registerform.details.last_name.data,
                date_of_birth=registerform.details.date_of_birth.data,
                phone_number=f"+{parsed_number.country_code} {parsed_number.national_number}",
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
            return redirect(url_for("storefront.home"))
        else:
            print("don't be here")
            flash("Passwords do not match")
            return redirect(url_for("storefront.home"))

    return render_template(
        "register.html", form=registerform, current_user=current_user
    )

@user_auth.route("/users/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    passwordform = UserPasswordChangeForm()
    if passwordform.validate_on_submit():
        if passwordform.password.data == passwordform.repeat.data:
            selected_user = db.get_or_404(User, current_user.id)
            selected_user.password = generate_password_hash(passwordform.password.data)
            db.session.commit()
            if current_user.role=="user":
                return redirect(url_for("user_control.show_user_details"))
            else:
                flash("Password has been changed")
                return redirect(url_for("user_auth.change_password"))
        else:
            flash("Passwords should match")
            return render_template("change-password.html", form=passwordform)
    return render_template("change-password.html", form=passwordform)

@user_auth.route("/users/reset-password", methods=["GET", "POST"])
def reset_password():
    print(SENDER)
    print(SENDER_PASSWORD)
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
            message = f"We've recieved a password reset request for your account\nHere's the link http://localhost:5000{url_for("user_auth.validate_reset", reset_token=trunc_hash.token)}\n\nIf you did not request this password reset to your account please ignore this email and consider changing your password."
            mailer.starttls()
            mailer.login(user=SENDER, password=SENDER_PASSWORD)
            mailer.sendmail(
                to_addrs=selected_user.email,
                from_addr="test@test.com",
                msg=f"Subject:Store user password reset\n\n{message}",
            )
        return render_template("confirm-reset.html")

    return render_template("reset-password.html", form=emailform)


@user_auth.route("/users/validate-reset", methods=["GET", "POST"])
def validate_reset():
    resetform = UserPasswordResetForm()

    token = request.args.get("reset_token")

    try:
        if resetform.validate_on_submit():
            if resetform.password.data==resetform.repeat.data:
                selected_token = db.session.execute(
                    db.select(ResetTokens).where(ResetTokens.token == resetform.token.data)
                ).scalar()
                decoded_token = jwt.decode(
                    resetform.token.data,
                    selected_token.username+selected_token.email,
                    algorithms="HS256",
                )
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
            else:
                flash("Passwords must match")
                return render_template("new-password.html", form=resetform, token=token)
        return render_template("new-password.html", form=resetform, token=token)
    except jwt.ExpiredSignatureError:
        flash("This password token has expired")
        return redirect(url_for("user_auth.reset_password"))
    except jwt.InvalidTokenError:
        flash("This password token is invalid")
        return redirect(url_for("user_auth.reset_password"))