from datetime import UTC, datetime
from functools import wraps

from fhir.resources.R4B.address import Address
from fhir.resources.R4B.annotation import Annotation
from fhir.resources.R4B.bundle import Bundle, BundleEntry
from fhir.resources.R4B.codeableconcept import CodeableConcept
from fhir.resources.R4B.coding import Coding
from fhir.resources.R4B.composition import Composition, CompositionSection
from fhir.resources.R4B.condition import Condition
from fhir.resources.R4B.contactpoint import ContactPoint
from fhir.resources.R4B.dosage import Dosage
from fhir.resources.R4B.encounter import Encounter, EncounterDiagnosis
from fhir.resources.R4B.humanname import HumanName
from fhir.resources.R4B.identifier import Identifier
from fhir.resources.R4B.medicationrequest import MedicationRequest
from fhir.resources.R4B.organization import Organization
from fhir.resources.R4B.patient import Patient
from fhir.resources.R4B.period import Period
from fhir.resources.R4B.practitioner import Practitioner
from fhir.resources.R4B.reference import Reference
from fhir.resources.R4B.resource import Resource

from abdm.models.health_facility import HealthFacility as HealthFacilityModel
from abdm.service.helper import uuid
from abdm.settings import plugin_settings as settings
from care.emr.models.base import EMRBaseModel
from care.emr.models.condition import Condition as ConditionModel
from care.emr.models.encounter import Encounter as EncounterModel
from care.emr.models.medication_request import (
    MedicationRequest as MedicationRequestModel,
)
from care.emr.models.patient import Patient as PatientModel
from care.emr.resources.condition.spec import ConditionSpecRead
from care.emr.resources.encounter.spec import EncounterRetrieveSpec
from care.emr.resources.facility.spec import FacilityRetrieveSpec
from care.emr.resources.medication.request.spec import MedicationRequestReadSpec
from care.emr.resources.patient.spec import PatientRetrieveSpec
from care.emr.resources.user.spec import UserRetrieveSpec
from care.facility.models import Facility as FacilityModel
from care.users.models import User as UserModel

CARE_IDENTIFIER_SYSTEM = settings.BACKEND_DOMAIN


class Fhir:
    def __init__(self):
        self._profiles = {}
        self._resource_id_url_map = {}

    @staticmethod
    def cache_profiles(resource_type: str):
        def decorator(func):
            @wraps(func)
            def wrapper(self, model_instance: EMRBaseModel, *args, **kwargs):
                if not hasattr(model_instance, "external_id"):
                    err = f"{model_instance.__class__.__name__} does not have 'external_id' attribute"
                    raise AttributeError(err)

                cache_key_prefix = kwargs.get("cache_key_prefix", "")
                cache_key_id = str(model_instance.external_id)
                cache_key_suffix = kwargs.get("cache_key_suffix", "")
                cache_key = f"{resource_type}/{cache_key_prefix}{cache_key_id}{cache_key_suffix}"

                if cache_key in self._profiles:
                    return self._profiles[cache_key]

                result = func(self, model_instance, *args, **kwargs)

                self._profiles[cache_key] = result
                self._resource_id_url_map[cache_key] = uuid()
                return result

            return wrapper

        return decorator

    def cached_profiles(self):
        return list(
            filter(lambda profile: profile is not None, self._profiles.values())
        )

    def _reference_url(self, resource: Resource = None):
        if resource is None:
            return ""

        key = f"{resource.resource_type}/{resource.id}"
        return f"urn:uuid:{self._resource_id_url_map.get(key, uuid())}"

    def _reference(self, resource: Resource = None):
        if resource is None:
            return None

        return Reference(reference=self._reference_url(resource))

    @cache_profiles(Patient.get_resource_type())
    def _patient(self, patient: PatientModel):
        patient_spec = PatientRetrieveSpec.serialize(patient)
        id = str(patient_spec.id)

        return Patient(
            id=id,
            identifier=[Identifier(value=id)],
            name=[HumanName(text=patient_spec.name)],
            telecom=[
                ContactPoint(system="phone", value=patient_spec.phone_number),
                ContactPoint(system="phone", value=patient_spec.emergency_phone_number),
            ],
            gender=patient_spec.gender,
            birthDate=patient.abha_number.date_of_birth,
            address=[
                Address(
                    line=[patient_spec.address],
                    postalCode=patient_spec.pincode,
                    country="IN",
                ),
                Address(
                    line=[patient_spec.permanent_address],
                    postalCode=patient_spec.pincode,
                    country="IN",
                ),
            ],
        )

    @cache_profiles(Practitioner.get_resource_type())
    def _practitioner(self, user: UserModel):
        user_spec = UserRetrieveSpec.serialize(user)
        id = str(user_spec.id)

        return Practitioner(
            id=id,
            identifier=[
                Identifier(
                    value=id,
                    type=CodeableConcept(
                        coding=[
                            Coding(
                                system="http://terminology.hl7.org/CodeSystem/v2-0203",
                                code="PRN",
                                display="Provider number",
                            )
                        ]
                    ),
                )
            ],
            name=[HumanName(text=user.full_name)],
            telecom=[
                ContactPoint(system="phone", value=user_spec.phone_number),
                ContactPoint(system="email", value=user_spec.email),
            ],
            gender=user_spec.gender,
            birthDate=user.date_of_birth,
        )

    @cache_profiles(Organization.get_resource_type())
    def _organization(self, facility: FacilityModel):
        health_facility = HealthFacilityModel.objects.filter(facility=facility).first()
        facility_spec = FacilityRetrieveSpec.serialize(facility)
        id = health_facility.hf_id if health_facility else str(facility_spec.id)

        return Organization(
            id=id,
            identifier=[
                Identifier(
                    system=(
                        "https://facility.ndhm.gov.in"
                        if health_facility
                        else f"{CARE_IDENTIFIER_SYSTEM}/facility"
                    ),
                    value=id,
                    type=CodeableConcept(
                        coding=[
                            Coding(
                                system="http://terminology.hl7.org/CodeSystem/v2-0203",
                                code="FI",
                                display="Facility ID",
                            )
                        ]
                    ),
                )
            ],
            type=[
                CodeableConcept(
                    coding=[
                        Coding(
                            system="http://terminology.hl7.org/CodeSystem/organization-type",
                            code="prov",
                            display="Healthcare Provider",
                        )
                    ]
                )
            ],
            name=facility_spec.name,
            telecom=[ContactPoint(system="phone", value=facility_spec.phone_number)],
            address=[
                Address(
                    line=[facility_spec.address],
                    postalCode=facility_spec.pincode,
                    country="IN",
                )
            ],
        )

    @cache_profiles(Condition.get_resource_type())
    def _condition(self, condition: ConditionModel):
        condition_spec = ConditionSpecRead.serialize(condition)
        id = str(condition_spec.id)

        return Condition(
            id=id,
            identifier=[Identifier(value=id)],
            category=[
                CodeableConcept(
                    coding=[
                        Coding(
                            system="http://terminology.hl7.org/CodeSystem/condition-category",
                            code=condition_spec.category,
                        )
                    ],
                )
            ],
            verificationStatus=CodeableConcept(
                coding=[
                    Coding(
                        system="http://terminology.hl7.org/CodeSystem/condition-ver-status",
                        code=condition_spec.verification_status,
                    )
                ]
            ),
            code=CodeableConcept(
                coding=[Coding(**condition_spec.code)],
            ),
            subject=self._reference(self._patient(condition.patient)),
        )

    @cache_profiles(Encounter.get_resource_type())
    def _encounter(self, encounter: EncounterModel, include_diagnosis: bool = False):
        encounter_spec = EncounterRetrieveSpec.serialize(encounter)
        id = str(encounter_spec.id)

        return Encounter(
            **{
                "id": id,
                "identifier": [Identifier(value=id)],
                "status": encounter_spec.status,
                "class": Coding(
                    system="http://terminology.hl7.org/CodeSystem/v3-ActCode",
                    code=encounter_spec.encounter_class,
                ),
                "subject": self._reference(self._patient(encounter.patient)),
                "priority": CodeableConcept(
                    coding=[
                        Coding(
                            system="http://terminology.hl7.org/CodeSystem/v3-ActPriority",
                            code=encounter_spec.priority,
                        )
                    ]
                ),
                "period": Period(**encounter_spec.period),
                "diagnosis": (
                    [
                        EncounterDiagnosis(
                            condition=self._reference(
                                self._condition(encounter_condition)
                            )
                        )
                        for encounter_condition in ConditionModel.objects.filter(
                            encounter=encounter
                        )
                    ]
                    if include_diagnosis
                    else None
                ),
            }
        )

    @cache_profiles(MedicationRequest.get_resource_type())
    def _medication_request(self, request: MedicationRequestModel):
        request_spec = MedicationRequestReadSpec.serialize(request)
        id = str(request_spec.id)

        return MedicationRequest(
            id=id,
            identifier=[Identifier(value=id)],
            status=request_spec.status,
            intent=request_spec.intent,
            authoredOn=request_spec.authored_on.isoformat(),
            dosageInstruction=[
                Dosage(**dosage) for dosage in request_spec.dosage_instruction
            ],
            note=[Annotation(text=request_spec.note)] if request_spec.note else None,
            medicationCodeableConcept=CodeableConcept(
                coding=[Coding(**request_spec.medication)],
            ),
            subject=self._reference(self._patient(request.patient)),
            requester=self._reference(self._practitioner(request.created_by)),
        )

    def _prescription_composition(
        self, requests: list[MedicationRequestModel], care_context_id: str
    ):
        return Composition(
            id=care_context_id,
            identifier=Identifier(
                value=care_context_id, system=f"{CARE_IDENTIFIER_SYSTEM}/composition"
            ),
            status="final",
            type=CodeableConcept(
                coding=[
                    Coding(
                        system="https://projecteka.in/sct",
                        code="440545006",
                        display="Prescription record",
                    )
                ]
            ),
            title="Prescription",
            date=datetime.now(UTC).isoformat(),
            section=[
                CompositionSection(
                    title="Prescription record",
                    code=CodeableConcept(
                        coding=[
                            Coding(
                                system="https://projecteka.in/sct",
                                code="440545006",
                                display="Prescription record",
                            )
                        ]
                    ),
                    entry=[
                        self._reference(self._medication_request(request))
                        for request in requests
                    ],
                )
            ],
            subject=self._reference(self._patient(requests[0].patient)),
            encounter=self._reference(self._encounter(requests[0].encounter)),
            author=[
                self._reference(self._organization(requests[0].encounter.facility))
            ],
        )

    def _bundle_entry(self, resource: Resource):
        return BundleEntry(fullUrl=self._reference_url(resource), resource=resource)

    def create_prescription_record(
        self,
        prescriptions: list[MedicationRequestModel],
        care_context_id: str = uuid(),
    ):
        return Bundle(
            id=care_context_id,
            identifier=Identifier(
                value=care_context_id, system=f"{CARE_IDENTIFIER_SYSTEM}/bundle"
            ),
            type="document",
            timestamp=datetime.now(UTC).isoformat(),
            entry=[
                self._bundle_entry(
                    self._prescription_composition(prescriptions, care_context_id)
                ),
                *[self._bundle_entry(profile) for profile in self.cached_profiles()],
            ],
        )
