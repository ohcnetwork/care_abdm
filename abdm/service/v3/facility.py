import re
from typing import Any, Dict

from abdm.service.helper import ABDMAPIException
from abdm.service.request import Request
from abdm.service.v3.types.facility import (
    AddUpdateServiceBody,
    AddUpdateServiceResponse,
)
from abdm.settings import plugin_settings as settings


class FacilityService:
    request = Request(f"{settings.ABDM_FACILITY_URL}/v1")

    @staticmethod
    def handle_error(error: Dict[str, Any] | str) -> str:
        if isinstance(error, list):
            return FacilityService.handle_error(error[0])

        if isinstance(error, str):
            return error

        # { error: { message: "error message" } }
        if "error" in error:
            return FacilityService.handle_error(error["error"])

        # { message: "error message" }
        if "message" in error:
            return error["message"]

        # { field_name: "error message" }
        if isinstance(error, dict) and len(error) >= 1:
            error.pop("code", None)
            error.pop("timestamp", None)
            return "".join(list(map(lambda x: str(x), list(error.values()))))

        return "Unknown error occurred at ABDM's end while processing the request. Please try again later."

    @staticmethod
    def add_update_service(
        data: AddUpdateServiceBody,
    ) -> AddUpdateServiceResponse:
        health_facility = data.get("health_facility")

        if not health_facility:
            raise ABDMAPIException(detail="Health Facility is required to add/update service")

        clean_facility_name = re.sub(r"[^A-Za-z0-9 ]+", " ", health_facility.facility.name)
        clean_facility_name = re.sub(r"\s+", " ", clean_facility_name).strip()
        hip_name = settings.ABDM_HIP_NAME_PREFIX + clean_facility_name + settings.ABDM_HIP_NAME_SUFFIX
        payload = {
                "facilityId": health_facility.hf_id,
                "facilityName": hip_name,
                "HRP": [
                    {
                        "bridgeId": settings.ABDM_CLIENT_ID,
                        "hipName": hip_name,
                        "type": "HIP",
                        "active": True,
                        "alias": ["CARE_HIP"],
                    }
                ],
            }

        path = "/bridges/MutipleHRPAddUpdateServices"
        response = FacilityService.request.post(
            path,
            payload,
        )

        if response.status_code != 200:
            raise ABDMAPIException(detail=FacilityService.handle_error(response.json()))

        return response
