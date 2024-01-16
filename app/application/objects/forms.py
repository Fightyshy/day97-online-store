import datetime as dt
import json
from flask import url_for
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
import phonenumbers
from wtforms import (
    DecimalField,
    HiddenField,
    IntegerField,
    PasswordField,
    StringField,
    DateField,
    SelectField,
    BooleanField,
    SubmitField,
    TextAreaField,
    FormField,
    TelField
)
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    Regexp,
    NumberRange,
    ValidationError,
)

with open("application/static/assets/json/phone.json") as phone:
    data = json.load(phone)


# User/Customer forms


# Use address form for billing
class AddressForm(FlaskForm):
    """Address form class for billing address, can resuse if shipping address is same"""

    address_one = StringField("Line one", validators=[DataRequired()])
    address_two = StringField("Line two")
    state = StringField("State/Province")
    city = StringField("City", validators=[DataRequired()])
    postal_code = StringField(
        "Postal Code", validators=[DataRequired(), Length(min=5)]
    )
    country = SelectField(
        "Country",
        choices=[key for key in data.keys()],
        validators=[DataRequired()],
    )
    same_number = BooleanField(
        "Phone number is same as in details",
        default=False,
    )
    phone_number = TelField("Phone number", validators=[DataRequired()])

    # custom validator for phone numbers
    def validate_phone_number(self, phone_number):
        try:
            number = phonenumbers.parse(phone_number.data)
            if not phonenumbers.is_valid_number(number):
                raise ValueError()
        except (phonenumbers.phonenumberutil.NumberParseException, ValueError):
            raise ValidationError("Invalid phone number entered")

    submit = SubmitField("Save address")


# Inherit fields from addressform, use fields if not same as billing
class ShippingAddress(AddressForm):
    """If shipping address is different from billing address,
    use this inherited form with a button to check inherited field state"""

    same_as_billing = BooleanField(
        "Shipping address is same as billing address",
        validators=[DataRequired()],
        default=False,
    )

    submit = SubmitField("Save shipping address")


class CustomerDetailsForm(FlaskForm):
    """Customer details form, both add on registration and edit"""

    first_name = StringField("First name", validators=[DataRequired()])
    last_name = StringField("Last name", validators=[DataRequired()])
    date_of_birth = DateField("Date of birth", validators=[DataRequired()])
    phone_number = TelField("Phone number", validators=[DataRequired()])

    # custom validator for phone numbers
    def validate_phone_number(self, phone_number):
        try:
            number = phonenumbers.parse(phone_number.data)
            if not phonenumbers.is_valid_number(number):
                raise ValueError()
        except (phonenumbers.phonenumberutil.NumberParseException, ValueError):
            raise ValidationError("Invalid phone number entered")

    submit = SubmitField("Save details")


class UserForm(FlaskForm):
    """User login form"""

    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class UserRegistrationForm(UserForm):
    """User registration form inherits login form fields"""

    # No need for def self and super according to docs
    repeat_password = PasswordField(
        "Repeat password", validators=[DataRequired()]
    )
    username = StringField("Username", validators=[DataRequired()])
    details = FormField(CustomerDetailsForm)
    submit = SubmitField("Register")


class UserPasswordResetEmailForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Send reset link")


class UserPasswordChangeForm(FlaskForm):
    password = PasswordField("Password", validators=[DataRequired()])
    repeat = PasswordField("Repeat password", validators=[DataRequired()])
    submit = SubmitField("Change password")


class UserPasswordResetForm(UserPasswordChangeForm):
    token = HiddenField(validators=[DataRequired()])
    submit = SubmitField("Reset password")


class UserEditRoleForm(FlaskForm):
    role = SelectField(
        "Role",
        choices=["admin", "employee", "user"],
        validators=[DataRequired()],
    )
    submit = SubmitField("Save role")


# Online store forms


class ProductForm(FlaskForm):
    """New/Edit product form"""

    name = StringField("Product name", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[DataRequired()])
    price = DecimalField(
        "Price", validators=[DataRequired(), NumberRange(min=1, max=99999)]
    )
    stock = IntegerField(
        "Quantity in stock", validators=[DataRequired(), NumberRange(min=1)]
    )
    # Upload from user's pc to server, save in same root as loc under assets/images
    # jpgs or pngs only, transform image to equiv 200x200px?
    image = FileField("Thumbnail Image (200x200px)", validators=[FileAllowed(["jpg", "png", "jpeg"], "JPG/PNG only")])
    category = SelectField(
        "Category",
        choices=[
            "Wargame Rulebooks",
            "Miniatures",
            "Dice",
            "Accessories",
            "Roleplaying Rulebooks",
        ],
        validators=[DataRequired()],
    )
    submit = SubmitField("Save product")


class ProductStockForm(FlaskForm):
    """For editting product stock levels"""

    stock = IntegerField(
        "Quantity in stock", validators=[DataRequired(), NumberRange(min=1)]
    )
    submit = SubmitField("Save stock")


class CommentForm(FlaskForm):
    """Add customer's comment and rating of a product form"""

    comment = TextAreaField(label="Comment", validators=[DataRequired()])
    rating = SelectField(
        "Rating",
        choices=["★", "★★", "★★★", "★★★★", "★★★★★"],
        default=["★"],
        validators=[DataRequired()],
    )
    submit = SubmitField("Add comment")
