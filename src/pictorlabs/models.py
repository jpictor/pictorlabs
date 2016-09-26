from __future__ import unicode_literals
import os
from django.db import models
from django.contrib.auth.models import User, Group
from django.contrib.postgres.fields import JSONField
from django.conf import settings


class Entity(models.Model):
    parent = models.ForeignKey('Entity', null=True, db_index=True, blank=True, on_delete=models.CASCADE)
    type = models.CharField(max_length=36, db_index=True)
    url = models.TextField(max_length=2048, db_index=True)
    image_url = models.TextField(max_length=2048, db_index=True, null=True, blank=True)
    title = models.TextField(max_length=2048, db_index=True, null=True, blank=True)
    key = models.TextField(max_length=2048, db_index=True, null=True, blank=True)
    user = models.ForeignKey(User, null=True, db_index=True, blank=True)
    doc = JSONField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, null=False)
    last_modified = models.DateTimeField(auto_now=True, null=False)

    class Meta:
        db_table = 'entity'
        get_latest_by = 'last_modified'
        ordering = ['last_modified']

    @property
    def storage_root(self):
        return os.path.join(settings.ENTITY_ROOT, str(self.id))

    @property
    def entity_baseurl(self):
        return u'{}/{}'.format(settings.ENTITY_BASEURL, self.id)

    def make_storage_root(self):
        try:
            os.makedirs(self.storage_root)
        except os.error:
            pass

    @property
    def video_path(self):
        if not self.key:
            raise Exception('key not set')
        return os.path.join(self.storage_root, self.key)


class FeatureSpace(models.Model):
    type = models.CharField(max_length=36, db_index=True, unique=True)

    class Meta:
        db_table = 'feature_space'


class Feature(models.Model):
    feature_set = models.ForeignKey(FeatureSpace, db_index=True, related_name='features')
    feature = models.CharField(max_length=256, db_index=True)

    class Meta:
        db_table = 'feature'
        unique_together = [('feature_set', 'feature')]


class EntityFeature(models.Model):
    entity = models.ForeignKey(Entity, related_name='entity_features')
    feature = models.ForeignKey(Feature, related_name='entity_features')
    weight = models.FloatField(default=0, db_index=True)
    timestamp = models.DateTimeField(db_index=True, null=True, auto_now=True)

    class Meta:
        db_table = 'entity_feature'
        unique_together = [('entity', 'feature')]


class EntityDocument(models.Model):
    entity = models.ForeignKey(Entity, related_name='entity_documents', db_index=True)
    type = models.CharField(max_length=36, db_index=True)
    doc = JSONField(null=True)
    created = models.DateTimeField(auto_now_add=True, null=False)
    last_modified = models.DateTimeField(auto_now=True, null=False)

    class Meta:
        db_table = 'entity_document'
        unique_together = ('entity', 'type')


