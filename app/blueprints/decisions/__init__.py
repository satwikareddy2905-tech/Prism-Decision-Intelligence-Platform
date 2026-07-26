from flask import Blueprint

decisions_bp = Blueprint('decisions', __name__, url_prefix='/decisions')
decisions_bp.strict_slashes = False


from . import routes  # noqa: F401, E402
