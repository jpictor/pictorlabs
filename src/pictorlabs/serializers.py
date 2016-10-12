from rest_framework import serializers
from django.contrib.auth.models import User, Group
from pictorlabs.models import Entity, EntityDocument


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')


class EntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity

    newspaper = serializers.SerializerMethodField()
    newspaper_timestamp = serializers.SerializerMethodField()
    topics = serializers.SerializerMethodField()
    num_children = serializers.SerializerMethodField()

    def get_topics(self, obj):
        entity_features = obj.entity_features.filter(feature__feature_set__type='topic').order_by('-weight')
        r = []
        for ef in entity_features:
            r.append(dict(topic=ef.feature.feature, weight=ef.weight))
        return r

    def get_newspaper(self, obj):
        entity_features = obj.entity_features.filter(feature__feature_set__type='newspaper').order_by('-weight')
        r = []
        for ef in entity_features:
            r.append(dict(topic=ef.feature.feature, weight=ef.weight))
        return r

    def get_newspaper_timestamp(self, obj):
        entity_features = obj.entity_features.filter(feature__feature_set__type='newspaper').first()
        if entity_features is None:
            return None
        return entity_features.timestamp

    def get_num_children(self, obj):
        return Entity.objects.filter(parent=obj.id).count()


class EntityDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntityDocument

