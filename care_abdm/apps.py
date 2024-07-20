from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

PLUGIN_NAME = "care_abdm"


class AbdmConfig(AppConfig):
    name = "care_abdm"
    verbose_name = _("ABDM Integration")
