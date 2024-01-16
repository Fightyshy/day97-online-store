from functools import wraps
from flask import render_template
from flask_login import current_user


def employee_check(f):
    """Checks if the current user is a admin or employee, renders error page with a 403 error if not"""

    @wraps(f)
    def dec_func(*args, **kwargs):
        if current_user.is_authenticated and (
            current_user.role == "admin" or "employee"
        ):
            return f(*args, **kwargs)
        else:
            return render_template("error.html", status=403)

    return dec_func


def admin_check(f):
    """Checks if current user is a admin, renders error page with a 403 error if not"""

    @wraps(f)
    def dec_func(*args, **kwargs):
        if current_user.is_authenticated and (current_user.role == "admin"):
            return f(*args, **kwargs)
        else:
            return render_template("error.html", status=403)

    return dec_func