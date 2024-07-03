from flask import request, g, current_app, Blueprint
import logging
from flask_login import login_required, login_manager
from geonature.core.gn_meta.routes import routes

log = logging.getLogger()
blueprint = Blueprint("mtd_sync", __name__)
from .mtd_sync import (
    sync_af_and_ds as mtd_sync_af_and_ds,
    sync_af_and_ds_by_user,
)


@current_app.before_request
def synchronize_mtd():
    if request.method != "OPTIONS" and request.endpoint in [
        "gn_meta.get_datasets",
        "gn_meta.get_acquisition_frameworks_list",
    ]:
        from flask_login import current_user

        try:
            sync_af_and_ds_by_user(id_role=current_user.id_role)
        except Exception as e:
            log.exception("Error while get JDD via MTD")
