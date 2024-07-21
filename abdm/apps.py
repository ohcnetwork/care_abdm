from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

PLUGIN_NAME = "abdm"


class AbdmConfig(AppConfig):
    name = "abdm"
    verbose_name = _("ABDM Integration")
