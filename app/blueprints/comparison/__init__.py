from flask import Blueprint

comparison_bp = Blueprint('comparison', __name__, url_prefix='/decisions')

from . import routes  # noqa: F401, E402
