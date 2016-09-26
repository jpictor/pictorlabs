
import pytz
from datetime import datetime, timedelta
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from django.http.response import HttpResponse
from rest_framework import status
from rest_framework import filters
from rest_framework.pagination import PageNumberPagination
import ujson as json
from baseapp.datetime_ext import datetime_from_isodate
from pictorlabs.serializers import (
    EntitySerializer,
    EntityDocumentSerializer
)
from pictorlabs.models import (
    Entity,
    EntityDocument,
    FeatureSpace,
    Feature,
    EntityFeature
)


class EntityViewSet(ModelViewSet):
    filter_backends = (filters.OrderingFilter, filters.DjangoFilterBackend)
    serializer_class = EntitySerializer
    filter_fields = ('type', 'parent')
    permission_classes = (AllowAny, )

    def get_queryset(self):
        parent_id = self.request.query_params.get('parent')
        if parent_id:
            qs = self.serializer_class.Meta.model.objects.all()
        else:
            qs = self.serializer_class.Meta.model.objects.filter(parent__isnull=True)
        return qs

    @detail_route(methods=['post'], url_path='set-features')
    def set_features(self, request, pk=None):
        entity = self.get_object()
        entity.entity_features.filter(feature__feature_set__type='topic').delete()
        data = JSONParser().parse(request)
        feature_set, created = FeatureSpace.objects.get_or_create(type='topic')
        for topic, weight in data.items():
            feature, created = Feature.objects.get_or_create(feature_set=feature_set, feature=topic)
            entity_feature, created = EntityFeature.objects.get_or_create(
                entity=entity, feature=feature, weight=weight)
        return Response(status=status.HTTP_200_OK)

    def set_entity_document(self, doc_type, request):
        data = JSONParser().parse(request)
        entity = self.get_object()
        entity_doc = entity.entity_documents.filter(type=doc_type).first()
        if not entity_doc:
            entity_doc = EntityDocument(entity=entity, type=doc_type)
        entity_doc.text = json.dumps(data)
        entity_doc.save()
        return Response(status=status.HTTP_200_OK)

    @detail_route(methods=['post'], url_path='set-test')
    def set_test_document(self, request, pk=None):
        return self.set_entity_document('test', request)

