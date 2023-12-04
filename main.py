from models import *
from flask import *

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///store.db"

db.init_app(app)

# sqlite db, will convert to local postgres db and dump creation script
# with app.app_context():
#     db.create_all()

@app.route("/")
def home():
    return "Test"

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


if __name__ == "__main__":
    app.run(debug=True)