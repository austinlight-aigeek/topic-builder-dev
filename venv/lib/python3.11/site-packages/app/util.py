from enum import Enum
from itertools import chain


def get_all_subclasses(cls):
    return list(
        chain.from_iterable([list(chain.from_iterable([[x], get_all_subclasses(x)])) for x in cls.__subclasses__()])
    )


def enum_to_list(e: Enum):
    return [str(v) for v in e]


def enum_to_dict(e: Enum):
    return [{str(v): str(v)} for v in e]
