import random
import string

from flask_sqlalchemy import SQLAlchemy

from ..models.models import Product, User


def generate_list_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def cart_merger(db: SQLAlchemy, current_user):
    selected_cart = db.get_or_404(
        User, current_user.id
    ).customerDetails.shoppingcart
    uids = [id.product_uid for id in selected_cart]
    products_in_cart = (
        db.session.execute(
            # in_ allows us to get from list of product_uids
            db.select(Product).where(Product.product_uid.in_(uids))
        )
        .scalars()
        .all()
    )
    truecart = []
    for item in selected_cart:
        for product in products_in_cart:
            if item.product_uid == product.product_uid:
                truecart.append({"cartobj": item, "productref": product})
    return truecart