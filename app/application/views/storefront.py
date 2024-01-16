from flask import Blueprint, render_template
from flask_login import current_user

from ..objects.forms import CommentForm
from ..models.models import User, db, Product, Comment
from sqlalchemy import or_

storefront = Blueprint("storefront", __name__, template_folder="templates")

@storefront.route("/")
def home():
    # join with comments to access comment.rating
    # group by product to consolidate dupes from children
    # having to filter based on product rating avg by threshold
    # featured_products = (
    #     db.session.execute(
    #         db.select(Product)
    #         .join(Product.comments)
    #         .group_by(Product)
    #         .having(func.avg(Comment.rating) >= 4)
    #     )
    #     .scalars()
    #     .all()
    # )

    # print([value.comments.rating for value in featured_products])
    # return render_template("index.html", featured=featured_products)
    return render_template("index.html")

@storefront.route("/products/category/<category>")
def show_category(category):
    if category == "rulebooks":
        products = db.session.execute(
            db.select(Product).where(
                or_(
                    Product.category == "Wargame Rulebooks",
                    Product.category == "Roleplaying Rulebooks",
                )
            )
        )
    elif category == "miniatures":
        products = db.session.execute(
            db.select(Product).where(Product.category == category.title())
        )
    elif category == "accessories":
        products = db.session.execute(
            db.select(Product).where(
                or_(
                    Product.category == "Dice",
                    Product.category == "Accessories",
                )
            )
        )
    return render_template(
        "product-category.html",
        products=products.scalars().all(),
        category=category,
    )

@storefront.route("/products/<int:product_id>", methods=["GET", "POST"])
def show_product(product_id):
    shown_product = db.get_or_404(Product, product_id)
    commentform = CommentForm()
    if commentform.validate_on_submit():
        selected_user = db.get_or_404(User, current_user.id)
        rating_val = len(commentform.rating.data)
        new_comment = Comment(
            comment=commentform.comment.data,
            rating=rating_val,
            product=shown_product,
            customer=selected_user.customerDetails,
        )
        db.session.add(new_comment)
        db.session.commit()
    return render_template(
        "product-detail.html",
        form=commentform,
        product=shown_product,
        product_id=product_id,
    )