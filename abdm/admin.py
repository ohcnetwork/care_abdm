from django.conf import settings
from django.contrib import admin

from .models import (
    AbhaNumber,
    ConsentArtefact,
    ConsentRequest,
    Transaction,
    HealthFacility,
)


@admin.register(AbhaNumber)
class AbhaNumberAdmin(admin.ModelAdmin):
    list_display = (
        "abha_number",
        "health_id",
        "patient",
        "name",
        "mobile",
    )
    search_fields = ("abha_number", "health_id", "name", "mobile")

    @admin.action(description="Delete selected ABHA number and consent records")
    def delete_abdm_records(self, request, queryset):
        ConsentArtefact.objects.filter(patient_abha__in=queryset).delete()
        ConsentRequest.objects.filter(patient_abha__in=queryset).delete()
        queryset.delete()
        self.message_user(
            request, "Selected ABHA number and consent records have been deleted"
        )

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not settings.IS_PRODUCTION:
            # delete_abdm_records should only be available in non-production environments
            actions["delete_abdm_records"] = self.get_action("delete_abdm_records")
        return actions


admin.site.register(ConsentArtefact)
admin.site.register(ConsentRequest)
admin.site.register(Transaction)
admin.site.register(HealthFacility)
