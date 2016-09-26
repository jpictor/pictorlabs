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
from pictorlabs.tasks import ProcessVideoMgr


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('video_url', type=unicode)

    def handle(self, *args, **options):
        video_url = options['video_url']
        mgr = ProcessVideoMgr(video_url)
        mgr.run_get_youtube_video()
        mgr.run_video_to_images()
        mgr.run_tag_video()

