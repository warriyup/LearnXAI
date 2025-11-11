from flask import Blueprint, render_template
blueprint = Blueprint('lite', __name__, template_folder='templates', static_folder='static')
@blueprint.route('/')
def home():
    return render_template('index.html')
