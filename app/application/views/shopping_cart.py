from flask import Blueprint, jsonify, render_template
from flask_login import current_user, login_required
from flask import (
    render_template,
    request
)
import stripe
import datetime as dt
from ..objects.helper_funcs import cart_merger, generate_list_id
from ..models.models import CustomerDetails, User, db, Product, Order, ShoppingCart

shopping_cart = Blueprint("shopping_cart", __name__, template_folder="templates")

ALLOWED = ["SG", "TH", "US", "GB", "JP", "MY", "AU"]

@shopping_cart.route("/shopping-cart")
@login_required
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

@shopping_cart.route("/cart/add-to-cart", methods=["POST"])
@login_required
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


@shopping_cart.route("/cart/remove-from-cart/<int:cart_id>", methods=["POST"])
@login_required
def remove_from_cart(cart_id):
    if request.method == "POST":
        selected_cart_item = db.get_or_404(ShoppingCart, cart_id)
        db.session.delete(selected_cart_item)
        db.session.commit()
        return ""


@shopping_cart.route("/cart/change-quantity", methods=["POST"])
@login_required
def change_product_quantity():
    if request.method == "POST":
        selected_cart_item = db.get_or_404(
            ShoppingCart, request.json["cart_id"]
        )
        selected_cart_item.quantity = request.json["quantity"]
        db.session.commit()
        return jsonify({"new_quantity": selected_cart_item.quantity})
    
@shopping_cart.route("/cart/checkout", methods=["GET", "POST"])
@login_required
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
@shopping_cart.route("/create-checkout-session", methods=["POST"])
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
            invoice_creation={"enabled": True},
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


@shopping_cart.route("/checkout-success")
@login_required
def successful_payment():
    # Reciept emails cannot be sent without fully activating a Stripe account, so no email reciepts
    # get cart first for invoicing
    # clean shopping cart of user
    selected_user = db.get_or_404(User, current_user.id)
    cart_items = db.session.execute(db.select(ShoppingCart).join(ShoppingCart.customer).where(CustomerDetails.id==selected_user.customerDetails.id)).scalars().all()
    # set orders
    # https://stackoverflow.com/questions/3659142/bulk-insert-with-sqlalchemy-orm
    # TODO debug - insert error customer not being inserted properly
    order_items = []
    for item in cart_items:
        while True:
            new_order_uid = generate_list_id()
            if db.session.execute(db.select(Order).where(Order.order_uid==new_order_uid)).scalar() is None:
                break
        invoice = Order(
            order_uid=new_order_uid,
            product_uid=item.product_uid,
            quantity=item.quantity,
            delivery_date=dt.datetime.now()+dt.timedelta(hours=120),
            customer=selected_user.customerDetails,
            customer_id=selected_user.customerDetails.id
        )
        order_items.append(invoice)

    db.session.bulk_save_objects(order_items)
    db.session.commit()

    # commit again for deletion
    # https://stackoverflow.com/questions/61574366/flask-sqlalchemy-bulk-deleting-records
    for delete_item in cart_items:
        db.session.delete(delete_item)
    db.session.commit()

    for order in order_items:
        selected_product = db.session.execute(db.select(Product).where(Product.product_uid==order.product_uid)).scalar()
        selected_product.stock -= order.quantity
    db.session.commit()

    # re-selected committed orders and present products based on uid
    grouped_order = db.session.execute(db.select(Order).where(Order.order_uid==order_items[0].order_uid)).scalars().all()
    present_products = {order.product_uid: db.session.execute(db.select(Product).where(Product.product_uid==order.product_uid)).scalar() for order in order_items}
    return render_template("successful_checkout.html", order=grouped_order, products=present_products, current_user=current_user)


@shopping_cart.route("/user/orders")
@login_required
def customer_orders():
    # db selection of all orders under user
    selected_user = db.get_or_404(User, current_user.id)
    selected_orders = db.session.execute(db.select(Order).join(Order.customer).where(CustomerDetails.id==selected_user.customerDetails.id)).scalars().all()

    # group orders and under order_uid and get all unique products based on order's product_uid
    grouped_orders = [{item.order_uid: db.session.execute(db.select(Order).where(Order.order_uid==item.order_uid)).scalars().all() for item in selected_orders}]
    present_products = {order.product_uid: db.session.execute(db.select(Product).where(Product.product_uid==order.product_uid)).scalar() for order in selected_orders}
    print(grouped_orders)
    print(present_products)
    return render_template("customer-orders.html", orders=grouped_orders, products=present_products, current_user=current_user)