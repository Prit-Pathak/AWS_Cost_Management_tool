# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import login_required, login_user, logout_user

import datetime
import boto3
from cloud_cost.extensions import login_manager
from cloud_cost.public.forms import LoginForm
from cloud_cost.user.forms import RegisterForm
from cloud_cost.user.models import User
from cloud_cost.utils import flash_errors

blueprint = Blueprint("public", __name__, static_folder="../static")


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    return User.get_by_id(int(user_id))


@blueprint.route("/", methods=["GET", "POST"])
def home():
    """Home page."""
    form = LoginForm(request.form)
    current_app.logger.info("Hello from the home page!")
    # Handle logging in
    if request.method == "POST":
        if form.validate_on_submit():
            login_user(form.user)
            flash("You are logged in.", "success")
            redirect_url = request.args.get("next") or url_for("user.members")
            return redirect(redirect_url)
        else:
            flash_errors(form)
    return render_template("public/home.html", form=form)


@blueprint.route("/logout/")
@login_required
def logout():
    """Logout."""
    logout_user()
    flash("You are logged out.", "info")
    return redirect(url_for("public.home"))


@blueprint.route("/register/", methods=["GET", "POST"])
def register():
    """Register new user."""
    form = RegisterForm(request.form)
    if form.validate_on_submit():
        User.create(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            active=True,
        )
        flash("Thank you for registering. You can now log in.", "success")
        return redirect(url_for("public.home"))
    else:
        flash_errors(form)
    return render_template("public/register.html", form=form)


@blueprint.route("/about/")
def about():
    """About page."""
    form = LoginForm(request.form)
    return render_template("public/about.html", form=form)

def fetch_aws_bills(start_date, end_date):
    # Create Boto3 Cost Explorer client
    session = boto3.Session(
        aws_access_key_id='AKIAQ3EGUD3FJYAPIWUV',
        aws_secret_access_key='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',
    )
    ce_client = session.client('ce')

    # Format start and end dates
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    # Fetch AWS cost and usage data
    response = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': start_date_str,
            'End': end_date_str
        },
        Granularity='MONTHLY',
        Metrics=['BlendedCost']
    )
    # Extract and return bill details
    bill_details = response['ResultsByTime']
    return bill_details

@blueprint.route("/aws/")
def billing():
    # Define start and end dates for the bill
    start_date = datetime.datetime(2024, 1, 14)
    end_date = datetime.datetime(2024, 2, 15)

    # Fetch AWS bills for the specified date range
    aws_bills = fetch_aws_bills(start_date, end_date)

    # Process the data as needed
    # Return the data to the template
    return render_template('public/billing.html', aws_bills=aws_bills)