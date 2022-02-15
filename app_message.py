from typing_extensions import TypedDict

class AppMessage(TypedDict):
    """
    AppMessage is a TypedDict that contains the information that is sent to the
    frontend.
    """
    id: str
    event: str
    payload: str