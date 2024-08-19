import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from abdm.service.helper import ABDMAPIException
from abdm.service.v3.gateway import GatewayService
from care.facility.models import PatientConsultation
from care.facility.models.notification import Notification
from care.utils.notification_handler import NotificationGenerator

logger = logging.getLogger(__name__)

@receiver(post_save, sender=PatientConsultation)
def create_care_context(sender, instance, created, **kwargs):
    patient = instance.patient

    if created and getattr(patient, "abha_number", None) is not None:
        try:
            GatewayService.link__carecontext(
                {
                    "consultations": [instance],
                    "link_token": None,
                }
            )
        except ABDMAPIException as e:
            # TODO: send a notification to the consultation.created_by to manually link the care_context
            logger.warning(
                f"Failed to link care context for consultation {instance.id} with patient {patient.id}, {str(e.detail)}"
            )

        except Exception as e:
            logger.exception(
                f"Failed to link care context for consultation {instance.id} with patient {patient.id}, {str(e)}"
            )
