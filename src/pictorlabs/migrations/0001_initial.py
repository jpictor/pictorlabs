# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-11 23:06
from __future__ import unicode_literals

from django.conf import settings
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Entity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(db_index=True, max_length=36)),
                ('url', models.URLField(db_index=True)),
                ('doc', django.contrib.postgres.fields.jsonb.JSONField(null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-last_modified'],
                'db_table': 'entity',
                'get_latest_by': 'last_modified',
            },
        ),
        migrations.CreateModel(
            name='EntityDocument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(db_index=True, max_length=36)),
                ('doc', django.contrib.postgres.fields.jsonb.JSONField(null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('entity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entity_documents', to='pictorlabs.Entity')),
            ],
            options={
                'db_table': 'entity_document',
            },
        ),
        migrations.CreateModel(
            name='EntityFeature',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weight', models.FloatField(db_index=True, default=0)),
                ('timestamp', models.DateTimeField(auto_now=True, db_index=True, null=True)),
                ('entity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entity_features', to='pictorlabs.Entity')),
            ],
            options={
                'db_table': 'entity_feature',
            },
        ),
        migrations.CreateModel(
            name='Feature',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('feature', models.CharField(db_index=True, max_length=256)),
            ],
            options={
                'db_table': 'feature',
            },
        ),
        migrations.CreateModel(
            name='FeatureSpace',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(db_index=True, max_length=36, unique=True)),
            ],
            options={
                'db_table': 'feature_space',
            },
        ),
        migrations.AddField(
            model_name='feature',
            name='feature_set',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='features', to='pictorlabs.FeatureSpace'),
        ),
        migrations.AddField(
            model_name='entityfeature',
            name='feature',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entity_features', to='pictorlabs.Feature'),
        ),
        migrations.AlterUniqueTogether(
            name='feature',
            unique_together=set([('feature_set', 'feature')]),
        ),
        migrations.AlterUniqueTogether(
            name='entityfeature',
            unique_together=set([('entity', 'feature')]),
        ),
        migrations.AlterUniqueTogether(
            name='entitydocument',
            unique_together=set([('entity', 'type')]),
        ),
    ]
