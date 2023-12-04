from flask_wtf import _Auto, FlaskForm
from pyparsing import Regex
from wtforms import StringField, DateField, SelectField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp
import datetime as dt

# User/Customer forms

# Use address form for billing
class AddressForm(FlaskForm):
    address_one = StringField("Line one", validators=[DataRequired()])
    address_two = StringField("Line two")
    state = StringField("State/Province", validators=[DataRequired()])
    city = StringField("City", validators=[DataRequired()])
    postal_code = StringField("Postal Code", validators=[DataRequired(),Length(min=5)])
    country = SelectField("Country", choices=[], validators=[DataRequired()])
    same_number = BooleanField("Phone number is same as in details", validators=[DataRequired()], default=False)
    phone_code = SelectField("Country code", choices=[], validators=[DataRequired()])
    phone_number = StringField("Phone number", validators=[Regexp("[0-9]{7,15}")])

# Inherit fields from addressform, use fields if not same as billing
class ShippingAddress(AddressForm):
    same_as_billing = BooleanField("Shipping address is same as billing address", validators=[DataRequired()], default=False)

class CustomerDetailsForm(FlaskForm):
    first_name = StringField("First name", filters=[str.lower(), str.strip()], validators=[DataRequired()])
    last_name = StringField("Last name", filters=[str.lower(), str.strip()], validators=[DataRequired()])
    date_of_birth = DateField("Date of birth", validators=[DataRequired()])
    phone_code = SelectField("Country code", choices=[], validators=[DataRequired()])
    phone_number = StringField("Phone number", validators=[DataRequired(), Regexp("[0-9]{7,15}")])

class UserForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = StringField("Password", validators=[DataRequired()])

class UserRegistrationForm(UserForm):
    # No need for def self and super according to docs
    repeat_password = StringField("Repeat password",validators=[DataRequired()])
    username = StringField("Username", validators=[DataRequired()])

# Online store forms