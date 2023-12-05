import datetime as dt
from flask_wtf import FlaskForm
from wtforms import (
    IntegerField,
    StringField,
    DateField,
    SelectField,
    BooleanField,
    FloatField,
    SubmitField,
)
from wtforms.validators import DataRequired, Email, Length, Regexp, NumberRange

# User/Customer forms


# Use address form for billing
class AddressForm(FlaskForm):
    """Address form class for billing address, can resuse if shipping address is same"""

    address_one = StringField("Line one", validators=[DataRequired()])
    address_two = StringField("Line two")
    state = StringField("State/Province", validators=[DataRequired()])
    city = StringField("City", validators=[DataRequired()])
    postal_code = StringField("Postal Code", validators=[DataRequired(), Length(min=5)])
    country = SelectField("Country", choices=[], validators=[DataRequired()])
    same_number = BooleanField(
        "Phone number is same as in details", validators=[DataRequired()], default=False
    )
    phone_code = SelectField("Country code", choices=[], validators=[DataRequired()])
    phone_number = StringField("Phone number", validators=[Regexp("[0-9]{7,15}")])

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
    phone_code = SelectField("Country code", choices=[], validators=[DataRequired()])
    phone_number = StringField(
        "Phone number", validators=[DataRequired(), Regexp("[0-9]{7,15}")]
    )
    submit = SubmitField("Save details")


class UserForm(FlaskForm):
    """User login form"""

    email = StringField("Email", validators=[DataRequired(), Email()])
    password = StringField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class UserRegistrationForm(UserForm):
    """User registration form inherits login form fields"""

    # No need for def self and super according to docs
    repeat_password = StringField("Repeat password", validators=[DataRequired()])
    username = StringField("Username", validators=[DataRequired()])
    submit = SubmitField("Register")

# Online store forms


class ProductForm(FlaskForm):
    """New/Edit product form"""

    name = StringField("Product name", validators=[DataRequired()])
    description = StringField("Description", validators=[DataRequired()])
    price = FloatField(
        "Price", validators=[DataRequired(), NumberRange(min=1, max=99999)]
    )
    stock = IntegerField(
        "Quantity in stock", validators=[DataRequired(), NumberRange(min=1)]
    )
    image = StringField(
        "Image", validators=[DataRequired()]
    )  # Upload from user's pc to server, save in same root as loc under /images
    category = SelectField("Category", choices=[], validators=[DataRequired()])
    submit = SubmitField("Add product")


class CommentForm(FlaskForm):
    """Add customer's comment and rating of a product form"""

    text = StringField(
        "Comment",
        validators=[
            DataRequired(),
            Length(1, 500, message="Please keep your comment within 500 characters"),
        ],
    )
    rating = SelectField(
        "Rating",
        choices=["★", "★★", "★★★", "★★★★", "★★★★★"],
        default=["★"],
        validators=[DataRequired()],
    )
    submit = SubmitField("Add comment")
