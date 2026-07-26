from flask import Blueprint

journal_bp = Blueprint('journal', __name__, url_prefix='/journal')

from . import routes  # noqa: F401, E402
