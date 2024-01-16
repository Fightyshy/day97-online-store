from flask import Blueprint, jsonify, render_template
from flask_login import current_user, login_required
from flask import (
    redirect,
    render_template,
    request,
    url_for,
)
from ..objects.forms import AddressForm, CustomerDetailsForm, UserEditRoleForm
from ..objects.auth_decor import employee_check, admin_check
from ..models.models import Address, User, db

user_control = Blueprint("user_control", __name__, template_folder="templates")

@user_control.route("/user")
@login_required
def show_user_details():
    # get id, check logged in or admin
    selected_user = db.get_or_404(User, current_user.id)
    addressform = AddressForm(request.form, csrf_enabled=True)
    customerdetailsform = CustomerDetailsForm(csrf_enabled=True)
    # render details and all addresses
    return render_template(
        "user-page.html",
        user=selected_user,
        current_user=current_user,
        form=addressform,
        detailform=customerdetailsform,
    )


@user_control.route("/edit-user", methods=["GET", "POST"])
@login_required
def edit_user_details():
    # get user, checked if logged in or admin
    selected_user = db.get_or_404(User, current_user.id)
    if request.method == "POST":
        # validate and submit changes to server
        customerdetailsform = CustomerDetailsForm(request.form)
        print(customerdetailsform.data)
        # TODO fix formating
        if customerdetailsform.validate():
            selected_user.customerDetails.first_name = (
                customerdetailsform.first_name.data
            )
            selected_user.customerDetails.last_name = (
                customerdetailsform.last_name.data
            )
            selected_user.customerDetails.date_of_birth = (
                customerdetailsform.date_of_birth.data
            )
            selected_user.customerDetails.phone_number = (
                customerdetailsform.phone_number.data
            )
            db.session.commit()
            return ""
    if selected_user.role == "user":
        return jsonify(
            {
                "customerDetails": {
                    "first_name": selected_user.customerDetails.first_name,
                    "last_name": selected_user.customerDetails.last_name,
                    "dob": selected_user.customerDetails.date_of_birth.strftime(
                        "%Y-%m-%d"
                    ),
                    "phone_number": selected_user.customerDetails.phone_number
                }
            }
        )


@user_control.route("/user/add-address", methods=["POST"])
@login_required
def add_address():
    addressform = AddressForm(request.form)
    # form validate and commit to db under address
    if addressform.validate_on_submit():
        # Get user
        selected_user = db.get_or_404(User, current_user.id)

        # check to see if same of diff number
        phone_number = (
            selected_user.customerDetails.phone_number
            if addressform.same_number.data is True
            else f"{addressform.phone_code} {addressform.phone_number}"
        )

        # Make new address obj
        new_address = Address(
            address_one=addressform.address_one.data,
            address_two=addressform.address_two.data,
            state=addressform.state.data,
            city=addressform.city.data,
            postcode=addressform.postal_code.data,
            country=addressform.country.data,
            phone_number=phone_number,
            customer=selected_user.customerDetails,
        )
        # Update customerDetails address with address
        selected_user.customerDetails.addresses.append(new_address)
        db.session.commit()
        return ""
    return "form for adding new address"


@user_control.route("/user/edit-address/<int:address_id>", methods=["GET", "POST"])
@login_required
def edit_address(address_id):
    # get address from address id, check if user id matches logged in user
    selected_user = db.get_or_404(User, current_user.id)
    selected_address = db.get_or_404(Address, address_id)
    if request.method == "POST":
        addressform = AddressForm(request.form)
        if addressform.validate():
            selected_address.address_one = addressform.address_one.data
            selected_address.address_two = addressform.address_two.data
            selected_address.state = addressform.state.data
            selected_address.city = addressform.city.data
            selected_address.postcode = addressform.postal_code.data
            selected_address.country = addressform.country.data
            selected_address.phone_number = addressform.phone_number.data
            db.session.commit()
            return ""

    if selected_address in selected_user.customerDetails.addresses:
        return jsonify(
            {
                "address": {
                    "address_one": selected_address.address_one,
                    "address_two": selected_address.address_two,
                    "state": selected_address.state,
                    "city": selected_address.city,
                    "postal_code": selected_address.postcode,
                    "country": selected_address.country,
                    "phone_number": selected_address.phone_number
                }
            }
        )


@user_control.route("/user/delete-address/<int:address_id>")
@login_required
def delete_address(address_id):
    selected_address = db.get_or_404(Address, address_id)
    db.session.delete(selected_address)
    db.session.commit()
    return redirect(url_for("user_control.show_user_details"))


# admin/employee control panel handling


@user_control.route("/users/control-panel", methods=["GET", "POST"])
@employee_check
@login_required
def user_control_panel():
    # get all users
    user_list = db.session.execute(db.select(User)).scalars().all()
    roleform = UserEditRoleForm()

    return render_template("user-control.html", users=user_list, form=roleform)


@user_control.route("/users/delete-user/<int:user_id>")
@admin_check
@login_required
def delete_user(user_id):
    selected_user = db.get_or_404(User, user_id)
    db.session.delete(selected_user)
    db.session.commit()
    return redirect(url_for("user_control.user_control_panel"))


@user_control.route("/users/edit-role/<int:user_id>", methods=["POST"])
@admin_check
@login_required
def edit_role(user_id):
    # handle AJAX
    if request.method == "POST":
        # recieve field inputs
        new_role = request.form.get("role")
        # select user and update user fields and commit
        selected_user = db.get_or_404(User, user_id)
        selected_user.role = new_role
        db.session.commit()
        return jsonify({"role": selected_user.role})
    # AJAX no redirect/render
    return ""