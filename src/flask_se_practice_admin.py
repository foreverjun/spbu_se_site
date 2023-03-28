# -*- coding: utf-8 -*-

from flask import flash, redirect, request, render_template, url_for

from flask_se_auth import login_required
from flask_login import current_user


@login_required
def index_admin():
    return render_template("practice/admin/base_practice_admin.html")
