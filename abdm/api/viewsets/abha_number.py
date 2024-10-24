from abdm.api.serializers.abha_number import AbhaNumberSerializer
from abdm.models import AbhaNumber, Transaction, TransactionType
from abdm.service.helper import uuid
from django.db.models import Q
from django.http import Http404
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from care.utils.queryset.patient import get_patient_queryset


class AbhaNumberViewSet(
    GenericViewSet,
    CreateModelMixin,
    RetrieveModelMixin,
):
    serializer_class = AbhaNumberSerializer
    model = AbhaNumber
    queryset = AbhaNumber.objects.all()
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        id = self.kwargs.get("pk")

        instance = self.queryset.filter(
            Q(abha_number=id) | Q(health_id=id) | Q(patient__external_id=id)
        ).first()

        if not instance or not get_patient_queryset(self.request.user).contains(
            instance.patient
        ):
            raise Http404

        self.check_object_permissions(self.request, instance)

        return instance

    def perform_create(self, serializer):
        instance = serializer.save()

        Transaction.objects.create(
            reference_id=uuid(),  # using random uuid as there is no transaction id for scan_and_pull
            type=TransactionType.CREATE_OR_LINK_ABHA_NUMBER,
            meta_data={
                "abha_number": str(instance.external_id),
                "method": "scan_and_pull",
            },
            created_by=self.request.user,
        )
