from typing import Dict

from py_arg.aspic.algorithms.justification.enum_justification_label import \
    EnumJustificationLabel
from py_arg.aspic.classes.literal import Literal


class LiteralLabels:
    def __init__(self,
                 literal_labeling: Dict[Literal, EnumJustificationLabel]):
        self.literal_labeling = literal_labeling

    def __getitem__(self, item):
        if not isinstance(item, Literal):
            raise ValueError(f'{item} is not a Literal!')
        return self.literal_labeling[item]

    def __eq__(self, other):
        return self.literal_labeling == other.literal_labeling
