from unittest.mock import patch

import pytest
from flask import url_for, g
import logging

from geonature.utils.env import db
from pypnusershub.tests.utils import set_logged_user
from sources.gn_module_mtd_sync.src.mtd_sync.mail_builder import MailBuilder

logger = logging.getLogger(__name__)


class TestMtd:
    def test_mtd(self):
        assert 1 == 1


@pytest.fixture
def users_with_mail(users):
    """
    Extend the fixture users by adding mails to every users
    """
    for user in users.values():
        user.email = f"{user.prenom_role}@example.com"
    db.session.commit()
    return users


@pytest.mark.usefixtures("client_class", "temporary_transaction")
class TestBlueprint:
    def test_extend_af_publication(
        self, app, users_with_mail, acquisition_frameworks, synthese_data, caplog
    ):
        """
        We check if the mechanism of extension of af publish works.
        """
        set_logged_user(self.client, users_with_mail["user"])
        af = acquisition_frameworks["af_1"]
        # Configure the extension by setting mtd_sync route as extended af publish route
        route_name = "mtd_sync.extended_af_publish"
        app.config["METADATA"]["EXTENDED_AF_PUBLISH_ROUTE_NAME"] = route_name
        with caplog.at_level(logging.ERROR):
            response = self.client.get(
                url_for(
                    "gn_meta.publish_acquisition_framework",
                    af_id=af.id_acquisition_framework,
                )
            )
        assert response.status_code == 500, response.json
        # We didn't setup mail sending so we only test if the connection refused error is in log when trying to send
        # mail. This is only present if we successfully called the route.
        assert (
            f" Erreur de type GeoNatureError lors de la publication du cadre : Custom route extended_af_publish "
            f"called on {af.id_acquisition_framework} raised : [Errno 111] Connection refused"
        ) in caplog.text

    def test_publish_acquisition_framework_mail_route(
        self, app, users_with_mail, acquisition_frameworks, synthese_data, caplog
    ):
        """
        We test our route by calling it directly
        """
        set_logged_user(self.client, users_with_mail["user"])
        af = acquisition_frameworks["af_1"]
        with caplog.at_level(logging.ERROR):
            response = self.client.get(
                url_for(
                    "mtd_sync.extended_af_publish",
                    af_id=af.id_acquisition_framework,
                )
            )
        # Same thing, the mail server is not configured so we check only if the right error is present
        assert response.status_code == 500
        assert "[Errno 111] Connection refused" in caplog.text


@pytest.mark.usefixtures("client_class", "temporary_transaction")
class TestMail:
    def test_mail_builder(self, app, users_with_mail, acquisition_frameworks):
        """
        Test if the mail builded correspond to what we expect
        """
        set_logged_user(self.client, users_with_mail["user"])
        af = acquisition_frameworks["af_1"]
        # We need to simulate a request context because the mail builder use the current user
        with app.test_request_context():
            g.current_user = users_with_mail["stranger_user"]
            mail_builder = MailBuilder(af)

        assert mail_builder.mail["recipients"] == ["Stranger@example.com"]
        assert (
            mail_builder.mail["subject"]
            == f"Dépôt du cadre d'acquisition {str(af.unique_acquisition_framework_id).upper()}"
        )
        assert "af_1" in mail_builder.mail["msg_html"]
        assert str(af.unique_acquisition_framework_id).upper() in mail_builder.mail["msg_html"]
