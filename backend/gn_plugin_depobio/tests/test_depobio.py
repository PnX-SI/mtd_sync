import os
from unittest.mock import patch

import pytest
from flask import url_for, g
import logging
from werkzeug.exceptions import Forbidden, NotFound
from gql.transport.exceptions import TransportQueryError

from geonature.utils.env import db
from gn_plugin_depobio.demarches_simplifiees import DemarchesSimplifieesConnection, ErrorCode
from pypnusershub.tests.utils import set_logged_user
from gn_plugin_depobio.mail_builder import MailBuilder

from gn_plugin_depobio.demarches_simplifiees.file import File
from .assets.api_responses import example_api_response

logger = logging.getLogger(__name__)


class TestDepobio:
    def test_Depobio(self):
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


def assert_file_properties(file):
    """Helper pour vérifier les propriétés d'un objet File"""
    assert file.id == "RG9zc2llci0zMzkxNTI5"
    assert file.number == 3391529
    assert file.libelle == "Projet-test"


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
        # Configure the extension by setting gn_plugin_depobio route as extended af publish route
        route_name = "plugin_depobio.extended_af_publish"
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
                    "plugin_depobio.extended_af_publish",
                    af_id=af.id_acquisition_framework,
                )
            )
        # Same thing, the mail server is not configured so we check only if the right error is present
        assert response.status_code == 500
        assert "[Errno 111] Connection refused" in caplog.text

    @patch(
        "gn_plugin_depobio.demarches_simplifiees.api.DemarchesSimplifieesConnection.is_valid_file_number"
    )
    def test_validate_file_number_error(self, mock_validate, app, users_with_mail):
        set_logged_user(self.client, users_with_mail["user"])
        mock_validate.side_effect = TransportQueryError(
            "a", errors=[{"extensions": {"code": ErrorCode.NOT_FOUND}}]
        )

        response_invalid = self.client.get(
            url_for(
                "plugin_depobio.validate_file_number",
                file_number=99999999,
            )
        )
        assert response_invalid.status_code == 404

    @patch(
        "gn_plugin_depobio.demarches_simplifiees.api.DemarchesSimplifieesConnection.is_valid_file_number"
    )
    def test_validate_file_number(self, mock_validate, app, users_with_mail):
        set_logged_user(self.client, users_with_mail["user"])
        mock_validate.return_value = True

        response_valid = self.client.get(
            url_for(
                "plugin_depobio.validate_file_number",
                file_number=3391529,
            )
        )
        assert response_valid.status_code == 200
        assert response_valid.json

    def get_file(self, file_number):
        return self.client.get(
            url_for(
                "plugin_depobio.get_file",
                file_number=file_number,
            )
        )

    @patch("gn_plugin_depobio.demarches_simplifiees.api.DemarchesSimplifieesConnection.get_file")
    def test_get_file_error(self, mock_get_file, app, users_with_mail):
        set_logged_user(self.client, users_with_mail["user"])
        mock_get_file.side_effect = TransportQueryError(
            "a", errors=[{"extensions": {"code": ErrorCode.FORBIDDEN}}]
        )
        response_invalid = self.get_file(99999999)
        assert response_invalid.status_code == 403

    @patch("gn_plugin_depobio.demarches_simplifiees.api.DemarchesSimplifieesConnection.get_file")
    def test_get_file(self, mock_get_file, app, users_with_mail):
        set_logged_user(self.client, users_with_mail["user"])
        mock_get_file.return_value = {
            "id": "RG9zc2llci0zMzkxNTI5",
            "number": 3391529,
            "libelle": "Projet-test",
        }
        response_valid = self.get_file(3391529)
        assert response_valid.status_code == 200
        file = response_valid.json
        assert file["id"] == "RG9zc2llci0zMzkxNTI5"
        assert file["number"] == 3391529
        assert file["libelle"] == "Projet-test"

    def test_get_af_from_file_number(self, app, users_with_mail, acquisition_frameworks):
        """
        Test retrieval of AF IDs from a file number
        """
        set_logged_user(self.client, users_with_mail["user"])

        af = acquisition_frameworks["af_1"]
        af.additional_data = {"file_id": "12345"}
        db.session.commit()

        response = self.client.get(
            url_for("plugin_depobio.get_af_from_file_number", file_number=12345)
        )
        assert response.status_code == 200
        assert response.json == [af.id_acquisition_framework]

        response_404 = self.client.get(
            url_for("plugin_depobio.get_af_from_file_number", file_number=99999)
        )
        assert response_404.status_code == 404

    def test_get_af_from_file_number_multiple(self, app, users_with_mail, acquisition_frameworks):
        """
        Test retrieval of multiple AF IDs linked to the same file number
        """
        set_logged_user(self.client, users_with_mail["user"])

        af1 = acquisition_frameworks["af_1"]
        af2 = acquisition_frameworks["af_2"]
        af1.additional_data = {"file_id": "555"}
        af2.additional_data = {"file_id": "555"}
        db.session.commit()

        response = self.client.get(
            url_for("plugin_depobio.get_af_from_file_number", file_number=555)
        )
        assert response.status_code == 200
        assert len(response.json) == 2
        assert af1.id_acquisition_framework in response.json
        assert af2.id_acquisition_framework in response.json


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


class TestDSAPI:
    @pytest.mark.skipif(
        os.environ.get("GITHUB_ACTIONS") == "true",
        reason="API not callable from CI Github because requires white listed IP",
    )
    def test_validate_file_number(self):
        ds_api = DemarchesSimplifieesConnection()
        assert ds_api.is_valid_file_number(3391529)
        with pytest.raises(TransportQueryError):
            ds_api.is_valid_file_number(99999999)

    @pytest.mark.skipif(
        os.environ.get("GITHUB_ACTIONS") == "true",
        reason="API not callable from CI Github because requires white listed IP",
    )
    def test_get_file_information(self):
        ds_api = DemarchesSimplifieesConnection()
        result = ds_api.get_file(3391529)
        assert_file_properties(result)
        with pytest.raises(TransportQueryError):
            ds_api.get_file(99999999)


class TestDSObjects:
    def test_file(self):
        file = File.from_dict(example_api_response)
        assert_file_properties(file)
