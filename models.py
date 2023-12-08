from typing import List
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
import datetime as dt

# https://stackoverflow.com/questions/9692962/flask-sqlalchemy-import-context-issue/9695045#9695045 for seperation of model from main

db = SQLAlchemy()

# Customers and details handling


class User(UserMixin, db.Model):
    """Flask login user model, customer details should be null if role is
    'admin' or 'employee'"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    # customer, employee, admin
    role: Mapped[str] = mapped_column(String, default="user", nullable=False)

    # customerDetails nullable if employee/admin
    customerDetails: Mapped["CustomerDetails"] = relationship(back_populates="user")


class CustomerDetails(db.Model):
    """Customer's particulars, also parent of shopping cart, addresses,
    and order invoices, child of user model"""

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    date_of_birth: Mapped[dt.datetime] = mapped_column(Date(), nullable=False)
    phone_number: Mapped[str] = mapped_column(String, nullable=False)
    # Parent
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(
        back_populates="customerDetails", single_parent=True
    )  # single_parent=True enforces one parent
    # Children
    # shopping cart 1>many
    shoppingcart: Mapped[List["ShoppingCart"]] = relationship(back_populates="customer")
    # address 1>many
    addresses: Mapped[List["Address"]] = relationship(back_populates="customer")
    # orders
    orders: Mapped[List["Order"]] = relationship(back_populates="customer")
    # comments and ratings on products
    comments: Mapped[List["Comment"]] = relationship(back_populates="customer")

class Address(db.Model):
    """Customer address, child of customer details"""

    __tablename__ = "addresses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    address_one: Mapped[str] = mapped_column(String, nullable=False)
    address_two: Mapped[str] = mapped_column(String)
    state: Mapped[str] = mapped_column(String)
    city: Mapped[str] = mapped_column(String)
    postcode: Mapped[str] = mapped_column(String)
    country: Mapped[str] = mapped_column(String)

    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    customer: Mapped["CustomerDetails"] = relationship(
        back_populates="addresses", single_parent=True
    )

class ResetTokens(db.Model):
    """Password reset token temp store"""
    __tablename__ = "tokens"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    token: Mapped[str] = mapped_column(String, nullable=False)

class Comment(db.Model):
    """Customer comment made on product, customer details and product parent"""

    __tablename__ = "comments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(String(length=500), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # Either do total calc in flask or save to db.

    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    customer: Mapped["CustomerDetails"] = relationship(back_populates="comments")
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    product: Mapped["Product"] = relationship(back_populates="comments")

# Point of sale models


class ShoppingCart(db.Model):
    """Customer's shopping cart, child of customer's details, but is parent of one shopping cart
    Shopping cart of a user is formed from a select query on customer_id, and retrieves it.
    """

    __tablename__ = "shoppingcarts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Using a unique ID for shopping cart/order saving
    product_uid: Mapped[str] = mapped_column(String(length=10), nullable=False)
    # Server sets added time
    date_added: Mapped[dt.datetime] = mapped_column(
        Date(), nullable=False, default=dt.datetime.now().date()
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    customer: Mapped["CustomerDetails"] = relationship(back_populates="shoppingcart")

    # TODO 1>1 product

    # product: Mapped["Product"] = relationship()


class Order(db.Model):
    """Customer's sales invoice, generated AFTER checkout and store as part of order history reference, child of customer details, parent of list of products"""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_uid: Mapped[str] = mapped_column(String(length=10), nullable=False)
    order_date: Mapped[dt.datetime] = mapped_column(
        Date(), nullable=False, default=dt.datetime.now().date()
    )
    delivery_date: Mapped[dt.datetime] = mapped_column(
        Date(), nullable=False, default=dt.datetime.now().date()
    )
    status: Mapped[str] = mapped_column(String, default="pending", nullable=False)

    # TODO address, either service layer copy/paste or set as relationship
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    customer: Mapped["CustomerDetails"] = relationship(back_populates="orders")


class Product(db.Model):
    """Product data, has relationship with"""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_uid: Mapped[str] = mapped_column(String(length=10), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    image: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # comments on product
    comments: Mapped["Comment"] = relationship(back_populates="comments")

    # cart_id: Mapped[int] = mapped_column(ForeignKey("shoppingcarts.id"))
    # cart: Mapped["ShoppingCart"] = relationship(
    #     back_populates="product", single_parent=True
    # )