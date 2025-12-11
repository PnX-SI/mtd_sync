from enum import Enum

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from gql.transport.exceptions import TransportQueryError
from geonature.utils.config import config
from pathlib import Path

from .file import File

configuration_demarches_simplifiees = config["PLUGIN_DEPOBIO"]["DEMARCHES_SIMPLIFIEES"]


class ErrorCode(str, Enum):
    # Démarches Simplifiées mixes up Unauthorized and Forbidden
    FORBIDDEN = "unauthorized"
    NOT_FOUND = "not_found"


class DemarchesSimplifieesConnection:
    """
    Class for interaction with Démarches Simplifiées GraphQL API.
    """

    def __init__(self):
        url_api = configuration_demarches_simplifiees["URL"]
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {configuration_demarches_simplifiees['TOKEN']}",
        }
        transport = RequestsHTTPTransport(url=url_api, headers=headers, verify=True, retries=3)

        self.client = Client(transport=transport, fetch_schema_from_transport=True)

    def is_valid_file_number(self, file_number: int) -> bool:
        """
        Check if the file number is valid for Démarches Simplifiées.

        Parameters
        ----------
        file_number
        """
        query = gql(
            """
            query validateDossier($dossierNumber: Int!) {
                dossier(number: $dossierNumber) {
                    id
                }
            }
            """
        )
        self.client.execute(query, variable_values={"dossierNumber": int(file_number)})
        return True

    def get_file(self, file_number: int) -> File:
        """
        Get file information from démarche simplifiée.

        Parameters
        ----------
        file_number : int
            The file number to retrieve

        Returns
        -------
        dict
            The file information from démarche simplifiée, or None if the file cannot be found.
        """
        current_dir = Path(__file__).parent
        query_file = current_dir / "graphql" / "file.graphql"

        with open(query_file, "r") as f:
            query = gql(f.read())
        result = self.client.execute(query, variable_values={"dossierNumber": int(file_number)})
        return File.from_dict(result)
