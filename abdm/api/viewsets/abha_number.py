from django.db.models import Q
from django.http import Http404
from rest_framework.mixins import RetrieveModelMixin, CreateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from abdm.api.serializers.abha_number import AbhaNumberSerializer
from abdm.models import AbhaNumber
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

    def get_queryset(self):
        queryset = self.queryset
        patients = get_patient_queryset(self.request.user)
        return queryset.filter(patient__in=patients, deleted=False)

    def get_object(self):
        queryset = self.get_queryset()
        id = self.kwargs.get("pk")

        instance = queryset.filter(
            Q(abha_number=id) | Q(health_id=id) | Q(patient__external_id=id)
        ).first()

        if not instance:
            raise Http404

        self.check_object_permissions(self.request, instance)

        return instance
