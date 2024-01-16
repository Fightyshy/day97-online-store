import os
from flask import Blueprint, current_app, jsonify, render_template
from flask_login import login_required
from flask import (
    redirect,
    render_template,
    request,
    url_for,
)
from werkzeug.utils import secure_filename

from ..objects.helper_funcs import generate_list_id
from ..objects.forms import ProductForm, ProductStockForm
from ..objects.auth_decor import employee_check, admin_check
from ..models.models import db, Comment, Product

product_control = Blueprint("product_control", __name__, template_folder="templates")

DEFAULT_IMAGE = "assets/default-img/defaultimage.png" 

@product_control.route("/products/delete-comment/<int:comment_id>")
@employee_check
@login_required
def delete_comment(comment_id):
    selected_comment = db.get_or_404(Comment, comment_id)
    db.session.delete(selected_comment)
    db.session.commit()
    return redirect(
        url_for("storefront.show_product", product_id=selected_comment.product_id)
    )


@product_control.route("/products/control-panel", methods=["GET", "POST"])
@login_required
@employee_check
def product_control_panel():
    product_list = db.session.execute(db.select(Product)).scalars().all()
    productform = ProductForm()

    if productform.validate_on_submit():
        product_uid = generate_list_id()
        while True:
            if (
                db.session.execute(
                    db.select(Product).where(
                        Product.product_uid == product_uid
                    )
                ).scalar()
                is not None
            ):
                product_uid = generate_list_id()
            else:
                break
        # get image and secure filename
        image = productform.image.data
        set_image = DEFAULT_IMAGE if image is None else "assets/product-images/"+secure_filename(image.filename)
        new_product = Product(
            name=productform.name.data,
            product_uid=product_uid,
            description=productform.description.data,
            price=productform.price.data,
            stock=productform.stock.data,
            image=set_image,
            category=productform.category.data,
        )
        db.session.add(new_product)
        db.session.commit()

        # save image locally
        if image:
            image.save(os.path.join(current_app.root_path, "static/",set_image))
        return redirect(url_for("product_control.product_control_panel"))

    return render_template(
        "product-control.html", products=product_list, form=productform
    )


@product_control.route("/products/edit-stock/<int:product_id>", methods=["GET", "POST"])
@employee_check
@login_required
def edit_product_stock(product_id):
    selected_product = db.get_or_404(Product, product_id)
    if request.method == "POST":
        stockform = ProductStockForm(request.form)
        if stockform.validate():
            selected_product.stock = stockform.stock.data
            db.session.commit()
            return jsonify({"product": {"stock": selected_product.stock}})
    return jsonify({"product": {"stock": selected_product.stock}})


@product_control.route("/products/edit-product/<int:product_id>", methods=["GET", "POST"])
@employee_check
@login_required
def edit_product(product_id):
    # get product from db
    selected_product = db.get_or_404(Product, product_id)
    # recieve post request
    if request.method == "POST":
        # if you leave it alone, it will default the formdata to 
        # request.form.data and request.form.files
        # of the incoming request and fill the fields itself
        productform = ProductForm()
        if productform.validate():
            new_image = productform.image.data
            current_image = selected_product.image.split("/")[-1]
            # if current image is not defaultimage and was uploaded
            if current_image is not DEFAULT_IMAGE.split("/")[-1] and new_image is not None:
                # del/prune current image from static if not DEFAULT_IMAGE
                if current_image != DEFAULT_IMAGE.split("/")[-1]:
                    print("here")
                    print(os.path.join(current_app.root_path, "static/assets/product-images/", current_image))
                    os.remove(os.path.join(current_app.root_path, "static/assets/product-images/", current_image))
                # set new image
                set_image = "assets/product-images/"+secure_filename(new_image.filename)
                print(os.path.join(current_app.root_path, set_image))
                new_image.save(os.path.join(current_app.root_path, "static/",set_image))
                # set db record separately here
                selected_product.image = set_image
                
            
            # edit product from db contents with request
            selected_product.name = productform.name.data
            selected_product.description = productform.description.data
            selected_product.price = productform.price.data
            selected_product.stock = productform.stock.data
            selected_product.category = productform.category.data
            # commit changes
            db.session.commit()
            return ""
        else:
            return jsonify({"status": "not-found"})
    payload = jsonify(
        {
            "status": "ok",
            "product": {
                "name": selected_product.name,
                "description": selected_product.description,
                "price": selected_product.price,
                "stock": selected_product.stock,
                "category": selected_product.category
            },
        }
    )
    return payload


@product_control.route("/products/delete-product/<int:product_id>")
@admin_check
@login_required
def delete_product(product_id):
    selected_product = db.get_or_404(Product, product_id)
    db.session.delete(selected_product)
    db.session.commit()
    return redirect(url_for("product_control.product_control_panel"))