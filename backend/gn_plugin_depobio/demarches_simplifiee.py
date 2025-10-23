from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from gql.transport.exceptions import TransportQueryError
from geonature.utils.config import config

configuration_depobio = config["PLUGIN_DEPOBIO"]


class DemarcheSimplifieConnexion:
    """
    Class for interaction with Demarche Simplifiée GraphQL API
    """

    def __init__(self):
        url_api = configuration_depobio["DEMARCHE_SIMPLIFIEES_URL"]
        headers = {
            "Content-Type": "application/json",
            "Authorization": f'Bearer {configuration_depobio["DEMARCHE_SIMPLIFIEES_TOKEN"]}',
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
