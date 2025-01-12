import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from abdm.models import HealthInformationType
from abdm.service.helper import ABDMAPIException
from abdm.service.v3.gateway import GatewayService
from care.emr.models.medication_request import MedicationRequest
from care.facility.models import (
    DailyRound,
    InvestigationValue,
    PatientConsultation,
    SuggestionChoices,
)

logger = logging.getLogger(__name__)


# FIXME: Wire it with emr models
@receiver(post_save, sender=PatientConsultation)
def create_care_context_on_consultation_creation(
    sender, instance: PatientConsultation, created: bool, **kwargs
):
    patient = instance.patient

    if not created or getattr(patient, "abha_number", None) is None:
        return

    try:
        transaction.on_commit(
            lambda: GatewayService.link__carecontext(
                {
                    "patient": patient,
                    "care_contexts": [
                        {
                            "hi_type": (
                                HealthInformationType.DISCHARGE_SUMMARY
                                if instance.suggestion == SuggestionChoices.A
                                else HealthInformationType.OP_CONSULTATION
                            ),
                            "reference": f"v1::consultation::{instance.external_id}",
                            "display": f"Encounter on {instance.created_date.date()}",
                        }
                    ],
                    "user": instance.created_by,
                }
            )
        )
    except ABDMAPIException as e:
        # TODO: send a notification to the consultation.created_by to manually link the care_context
        warning = f"Failed to link care context for consultation {instance.external_id} with patient {patient.external_id}, {e.detail!s}"
        logger.warning(warning)

    except Exception as e:
        warning = f"Failed to link care context for consultation {instance.external_id} with patient {patient.external_id}, {e!s}"
        logger.exception(warning)


# FIXME: Wire it with emr models
# using investigation value over investigation session because of the values are created after session which makes consultation inaccessible
@receiver(post_save, sender=InvestigationValue)
def create_care_context_on_investigation_creation(
    sender, instance: InvestigationValue, created: bool, **kwargs
):
    patient = instance.consultation.patient
    investigation_values = InvestigationValue.objects.filter(session=instance.session)

    if (
        not patient
        or getattr(patient, "abha_number", None) is None
        or len(investigation_values) > 1
    ):
        return

    try:
        transaction.on_commit(
            lambda: GatewayService.link__carecontext(
                {
                    "patient": patient,
                    "care_contexts": [
                        {
                            "hi_type": HealthInformationType.DIAGNOSTIC_REPORT,
                            "reference": f"v1::investigation_session::{instance.session.external_id}",
                            "display": f"Investigation on {instance.session.created_date.date()}",
                        }
                    ],
                    "user": instance.session.created_by,
                }
            )
        )
    except ABDMAPIException as e:
        warning = f"Failed to link care context for investigation {instance.session.external_id} with patient {patient.external_id}, {e.detail!s}"
        logger.warning(warning)

    except Exception as e:
        warning = f"Failed to link care context for investigation {instance.session.external_id} with patient {patient.external_id}, {e!s}"
        logger.exception(warning)


# FIXME: Wire it with emr models
@receiver(post_save, sender=DailyRound)
def create_care_context_on_daily_round_creation(
    sender, instance: DailyRound, created: bool, **kwargs
):
    patient = instance.consultation.patient

    if not created or not patient or getattr(patient, "abha_number", None) is None:
        return

    try:
        transaction.on_commit(
            lambda: GatewayService.link__carecontext(
                {
                    "patient": patient,
                    "care_contexts": [
                        {
                            "hi_type": HealthInformationType.WELLNESS_RECORD,
                            "reference": f"v1::daily_round::{instance.external_id}",
                            "display": f"Daily Round on {instance.created_date.date()}",
                        }
                    ],
                    "user": instance.created_by,
                }
            )
        )
    except ABDMAPIException as e:
        warning = f"Failed to link care context for daily round {instance.external_id} with patient {patient.external_id}, {e.detail!s}"
        logger.warning(warning)

    except Exception as e:
        warning = f"Failed to link care context for daily round {instance.external_id} with patient {patient.external_id}, {e!s}"
        logger.exception(warning)


@receiver(post_save, sender=MedicationRequest)
def create_care_context_on_medication_request_creation(
    sender, instance: MedicationRequest, created: bool, **kwargs
):
    patient = instance.patient

    if (
        not created
        or not patient
        or getattr(patient, "abha_number", None) is None
        or MedicationRequest.objects.filter(
            encounter=instance.encounter,
            created_date__date=instance.created_date.date(),
        ).count()
        > 1
    ):
        return

    try:
        transaction.on_commit(
            lambda: GatewayService.link__carecontext(
                {
                    "patient": patient,
                    "care_contexts": [
                        {
                            "hi_type": HealthInformationType.PRESCRIPTION,
                            "reference": f"v2::medication_request::{instance.created_date.date()}",
                            "display": f"Medication Prescribed on {instance.created_date.date()}",
                        }
                    ],
                    "user": instance.created_by,
                }
            )
        )
    except ABDMAPIException as e:
        warning = f"Failed to link care context for medication request {instance.external_id} with patient {patient.external_id}, {e.detail!s}"
        logger.warning(warning)

    except Exception as e:
        warning = f"Failed to link care context for medication request {instance.external_id} with patient {patient.external_id}, {e!s}"
        logger.exception(warning)
