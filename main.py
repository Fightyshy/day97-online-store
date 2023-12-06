from flask_login import current_user
from models import db, Product, Comment
from flask import Flask, render_template
from forms import CommentForm
from sqlalchemy import func

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///store.db"

db.init_app(app)

# sqlite db, will convert to local postgres db and dump creation script
# with app.app_context():
#     db.create_all()


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
    return render_template("", featured=featured_products)


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
        product_id=product_id
    )


if __name__ == "__main__":
    app.run(debug=True)
