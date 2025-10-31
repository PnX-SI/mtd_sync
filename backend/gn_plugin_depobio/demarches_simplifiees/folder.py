import dataclasses
import datetime
from enum import Enum
from typing import Optional


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
    values: str = None
    selected: Optional[bool] = None
    date: Optional[datetime.date] = None


@dataclasses.dataclass()
class Fields:
    fields: list[Field]

    def __init__(self, fields: list[Field]):
        self.fields = fields
        self.__fields_as_dict = {field.id: field for field in fields}

    def get_libelle(self):
        return self.__fields_as_dict["Q2hhbXAtMTE0NzQ4"]

    def get_description(self):
        return self.__fields_as_dict["Q2hhbXAtMTE0NzQ5"]

    def get_date_fin(self):
        return self.__fields_as_dict["Q2hhbXAtMTE0Nzgy"]

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
class Folder:
    id: str
    number: int
    state: State
    libelle: str
    description: str
    date_fin: str
    _fields: Fields

    @classmethod
    def from_dict(cls, data: dict) -> "Folder":
        if "dossier" not in data:
            raise ValueError("Data should contain a 'dossier' key")
        folder_api = data["dossier"]
        champs = Fields.champs_from_list(folder_api["champs"] + folder_api["annotations"])
        return cls(
            folder_api["id"],
            folder_api["number"],
            State(folder_api["state"]),
            champs.get_libelle().stringValue,
            champs.get_description().stringValue,
            champs.get_date_fin().stringValue,
            champs,
        )
