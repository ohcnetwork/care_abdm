from typing import TypedDict

from abdm.models import HealthFacility


class AddUpdateServiceBody(TypedDict):
    health_facility: HealthFacility


class AddUpdateServiceResponse(TypedDict):
    pass
