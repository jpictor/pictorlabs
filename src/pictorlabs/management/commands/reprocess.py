import os
import glob
import numpy as np
from PIL import Image
import caffe
import requests
import skimage
from cStringIO import StringIO
from django.conf import settings
from django.core.management.base import BaseCommand
from pictorlabs.models import Entity
from pictorlabs.tasks import ProcessVideoMgr, add_video_task


class Command(BaseCommand):
    def add_arguments(self, parser):
        #parser.add_argument('video_url', type=unicode)
        pass

    def handle(self, *args, **options):
        entities = list(Entity.objects.filter(type='video'))
        for e in entities:
            add_video_task(e.url)
