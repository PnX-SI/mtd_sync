import dataclasses

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from gql.transport.exceptions import TransportQueryError
from geonature.utils.config import config
from pathlib import Path

from .folder import Folder

configuration_demarches_simplifiees = config["PLUGIN_DEPOBIO"]["DEMARCHES_SIMPLIFIEES"]


class DemarchesSimplifieesConnexion:
    """
    Class for interaction with Demarche Simplifiée GraphQL API
    """

    def __init__(self):
        url_api = configuration_demarches_simplifiees["URL"]
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {configuration_demarches_simplifiees['TOKEN']}",
        }
        transport = RequestsHTTPTransport(url=url_api, headers=headers, verify=True, retries=3)

        self.client = Client(transport=transport, fetch_schema_from_transport=True)

    def is_valid_folder_number(self, dossier_number: int) -> bool:
        """
        Validate if the folder number is valid for démarche simplifiée

        Parameters
        ----------
        dossier_number
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

        try:
            self.client.execute(query, variable_values={"dossierNumber": int(dossier_number)})
            return True
        except TransportQueryError:
            return False

    def get_folder(self, folder_number: int):
        """
        Get folder information from démarche simplifiée

        Parameters
        ----------
        folder_number : int
            The folder number to retrieve

        Returns
        -------
        dict
            The folder information from démarche simplifiée, or None if the folder cannot be found
        """
        current_dir = Path(__file__).parent
        query_file = current_dir / "graphql" / "folder.graphql"

        with open(query_file, "r") as f:
            query = gql(f.read())

        try:
            result = self.client.execute(
                query, variable_values={"dossierNumber": int(folder_number)}
            )
            return Folder.from_dict(result)
        except TransportQueryError:
            return None
