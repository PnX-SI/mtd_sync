import dataclasses
import datetime
from enum import Enum
from typing import Optional, List
from geonature.utils.config import config

configuration_depobio = config["PLUGIN_DEPOBIO"]


class State(str, Enum):
    EN_CONSTRUCTION = "en_construction"
    ACCEPTE = "accepte"
    EN_INSTRUCTION = "en_instruction"
    REFUSE = "refuse"
    SANS_SUITE = "sans_suite"


@dataclasses.dataclass()
class Field:
    id: str
    champDescriptorId: str
    _typename: str
    label: str
    stringValue: str
    prefilled: bool
    columns: list
    values: Optional[List[str]] = None
    selected: Optional[bool] = None
    date: Optional[datetime.date] = None


@dataclasses.dataclass()
class Fields:
    fields: list[Field]

    def __init__(self, fields: list[Field]):
        self.fields = fields
        self.__fields_as_dict = {field.id: field for field in fields}
        self.configuration = configuration_depobio["DEMARCHES_SIMPLIFIEES"]

    def _get_field_by_config_key(self, config_key: str) -> Field:
        """
        Retrieves a field object based on the specified configuration key.

        Parameters
        ----------
        config_key : str
            The key representing the desired configuration to retrieve the associated field.

        Returns
        -------
        Field
            The field object associated with the provided configuration key.

        Raises
        ------
        ValueError
            If the field ID retrieved from the configuration does not exist in the internal
            dictionary of fields.
        """
        field_id = self.configuration[config_key]
        try:
            return self.__fields_as_dict[field_id]
        except KeyError as err:
            raise ValueError(
                f"The value supplied in the configuration for {config_key}"
                f" - {field_id} - appears to be wrong. Check your config."
            ) from err

    def get_libelle(self):
        return self._get_field_by_config_key("LIBELLE_ID")

    def get_description(self):
        return self._get_field_by_config_key("DESCRIPTION_ID")

    def get_date_fin(self):
        return self._get_field_by_config_key("DATE_FIN_ID")

    @classmethod
    def champs_from_list(cls, fields: list[dict]) -> "Fields":
        fields_result = []
        for champ in fields:
            # We make copies so popping doesn't affect the original list
            champ_copy = champ.copy()
            # double underscore mess with python name mangling
            champ_copy["_typename"] = champ_copy.pop("__typename")
            fields_result.append(champ_copy)
        return cls([Field(**champ_copy) for champ_copy in fields_result])

    def __repr__(self):
        return repr(self.fields)


@dataclasses.dataclass
class File:
    id: str
    number: int
    state: State
    libelle: str
    description: str
    date_fin: str
    contractor: str
    siret: str
    _fields: Fields

    @classmethod
    def from_dict(cls, data: dict) -> "File":
        if "dossier" not in data:
            raise ValueError("Data should contain a 'dossier' key")
        file = data["dossier"]
        champs = Fields.champs_from_list(file["champs"] + file["annotations"])
        siret = file["demandeur"]["entreprise"]["siretSiegeSocial"]
        contractor = file["demandeur"]["entreprise"]["raisonSociale"]
        return cls(
            file["id"],
            file["number"],
            State(file["state"]),
            champs.get_libelle().stringValue,
            champs.get_description().stringValue,
            champs.get_date_fin().stringValue,
            contractor,
            siret,
            champs,
        )
