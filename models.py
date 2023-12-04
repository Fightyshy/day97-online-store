from enum import Enum
from typing import List
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import datetime as dt

# https://stackoverflow.com/questions/9692962/flask-sqlalchemy-import-context-issue/9695045#9695045 for seperation of model from main

db = SQLAlchemy()

# Customers

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    # customer, employee, admin
    role: Mapped[str] = mapped_column(String, default="user", nullable=False)

    # customerDetails nullable if employee/admin
    customerDetails: Mapped["Customer"] = relationship("Customer")  # type: ignore

class CustomerDetails(db.Model):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    date_of_birth: Mapped[dt.datetime] = mapped_column(Date(), nullable=False)
    phone_number: Mapped[str] = mapped_column(String, nullable=False)
    
    # Parent
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="customerDetails", single_parent=True) # single_parent=True enforces one parent 

    # Children
    # shopping cart 1>many
    shoppingcart: Mapped[List["ShoppingCart"]] = relationship(back_populates="customer")
    # address 1>many
    addresses: Mapped[List["Address"]] = relationship(back_populates="customer")
    # orders
    orders: Mapped[List["Order"]] = relationship(back_populates="customer")

class Address(db.Model):
    __tablename__ = "addresses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    address_one: Mapped[str] = mapped_column(String, nullable=False)
    address_two: Mapped[str] = mapped_column(String)
    state: Mapped[str] = mapped_column(String)
    city: Mapped[str] = mapped_column(String)
    postcode: Mapped[str] = mapped_column(String)
    country: Mapped[str] = mapped_column(String)

    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    customer: Mapped["CustomerDetails"] = relationship(back_populates="addresses", single_parent=True)

# Point of sale models
class ShoppingCart(db.Model):
    __tablename__ = "shoppingcarts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Server sets added time
    date_added: Mapped[dt.datetime] = mapped_column(Date(), nullable=False, server_default=func.now())
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    customer: Mapped["CustomerDetails"] = relationship(back_populates="shoppingcart")

    # TODO 1>1 product

    product: Mapped["Product"] = relationship()

class Order(db.Model):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    order_date: Mapped[dt.datetime] = mapped_column(Date(), nullable=False, server_default=func.now())
    delivery_date: Mapped[dt.datetime] = mapped_column(Date(), nullable=False, server_default=func.now())
    status: Mapped[str] = mapped_column(Enum('pending', 'delivered'), default='pending')
    
    # TODO address, either service layer copy/paste or set as relationship
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    customer: Mapped["CustomerDetails"] = relationship(back_populates="orders")


class Product(db.Model):
    __tablename__ = "products"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    image: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    cart_id: Mapped[int] = mapped_column(ForeignKey("shoppingcarts.id"))
    cart: Mapped["ShoppingCart"] = relationship(back_populates="product", single_parent=True)