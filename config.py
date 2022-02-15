from typing_extensions import TypedDict


class Config(TypedDict):
    """
    Config is a TypedDict that contains the information that is read from the
    config file.
    """
    endpoint: str
    device_id: str
