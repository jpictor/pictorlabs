import os
import shutil
import glob
import numpy as np
import requests
from PIL import Image
import caffe
import requests
import skimage
import cv2
from cStringIO import StringIO
from django.conf import settings
from django.core.management.base import BaseCommand
from pictorlabs.models import Entity
from pytube import YouTube
from baseapp.run_ext import run_with_io_timeout
from baseapp.celery_ext import app


#bvlc_reference_caffenet_model = (
#    'models/bvlc_reference_caffenet/deploy.prototxt',
#    'models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel',
#    227, 227,
#    'python/caffe/imagenet/ilsvrc_2012_mean.npy',
#    'data/ilsvrc12/synset_words.txt')


bvlc_googlenet_model = (
    os.path.join(settings.DATA_ROOT, 'caffe/bvlc_googlenet/deploy.prototxt'),
    os.path.join(settings.DATA_ROOT, 'caffe/bvlc_googlenet/bvlc_googlenet.caffemodel'),
    224, 224,
    os.path.join(settings.DATA_ROOT, 'caffe/bvlc_googlenet/ilsvrc_2012_mean.npy'),
    os.path.join(settings.DATA_ROOT, 'caffe/bvlc_googlenet/synset_words.txt')
)


def set_gpu_if_exists():
    caffe.set_device(0)
    caffe.set_mode_gpu()
    #caffe.set_mode_cpu()


class ImageModel(object):
    @classmethod
    def new_image_model(cls, model_name):
        models = {
            'bvlc_googlenet': bvlc_googlenet_model
        }
        return cls(*models[model_name])

    def __init__(self, prototxt_path, caffemodel_path, width, height, mean_image_path, labels_path):
        self.deploy_prototext_path = prototxt_path
        self.caffemodel_path = caffemodel_path
        self.width = width
        self.height = height
        self.imagenet_mean_path = mean_image_path
        self.labels_path = labels_path

        set_gpu_if_exists()

        self.text_labels = np.loadtxt(self.labels_path, str, delimiter='\t')
        self.net = caffe.Net(self.deploy_prototext_path, self.caffemodel_path, caffe.TEST)

        # load input and configure preprocessing
        self.transformer = caffe.io.Transformer({'data': self.net.blobs['data'].data.shape})
        mean = np.load(self.imagenet_mean_path).mean(1).mean(1)
        #print('mean = {}'.format(mean.shape))
        #raise SystemExit(-1)
        self.transformer.set_mean('data', mean)
        self.transformer.set_transpose('data', (2,0,1))
        self.transformer.set_channel_swap('data', (2,1,0))
        self.transformer.set_raw_scale('data', 255.0)

        # note we can change the batch size on-the-fly
        # since we classify only one image, we change batch size from 10 to 1
        self.net.blobs['data'].reshape(1,3,self.width,self.height)

    def image_labels(self, image_path):
        im = caffe.io.load_image(image_path)
        self.net.blobs['data'].data[...] = self.transformer.preprocess('data', im)
        out = self.net.forward()
        predicted_class = out['prob'].argmax()
        output_prob = self.net.blobs['prob'].data[0]
        # sort top five predictions from softmax output
        top_inds = output_prob.argsort()[::-1][:5]
        return [(float(x), y) for x, y in zip(output_prob[top_inds], self.text_labels[top_inds])]


class FaceGenderAgeImageModel(object):
    @classmethod
    def new_image_model(cls, model_name):
        if model_name == 'gender':
            return cls(
                os.path.join(settings.DATA_ROOT, 'caffe/cnn_age_gender_models_and_data.0.0.2/deploy_gender.prototxt'),
                os.path.join(settings.DATA_ROOT, 'caffe/cnn_age_gender_models_and_data.0.0.2/gender_net.caffemodel'),
                os.path.join(settings.DATA_ROOT, 'caffe/cnn_age_gender_models_and_data.0.0.2/mean.binaryproto'),
                ['Male', 'Female']
            )

        elif model_name == 'age':
            return cls(
                os.path.join(settings.DATA_ROOT, 'caffe/cnn_age_gender_models_and_data.0.0.2/deploy_age.prototxt'),
                os.path.join(settings.DATA_ROOT, 'caffe/cnn_age_gender_models_and_data.0.0.2/age_net.caffemodel'),
                os.path.join(settings.DATA_ROOT, 'caffe/cnn_age_gender_models_and_data.0.0.2/mean.binaryproto'),
                ['(0, 2)','(4, 6)','(8, 12)','(15, 20)','(25, 32)','(38, 43)','(48, 53)','(60, 100)']
            )

    def __init__(self, prototxt_path, caffemodel_path, mean_image_path, class_labels):
        self.deploy_prototext_path = prototxt_path
        self.caffemodel_path = caffemodel_path
        self.mean_image_path = mean_image_path
        self.class_labels = class_labels
        set_gpu_if_exists()
        proto_data = open(self.mean_image_path, 'rb').read()
        a = caffe.io.caffe_pb2.BlobProto.FromString(proto_data)
        mean = caffe.io.blobproto_to_array(a)[0]
        mean = mean.mean(1).mean(1)
        print('mean = {}'.format(mean.shape))
        #raise SystemExit(-1)
        self.classifier = caffe.Classifier(
            self.deploy_prototext_path,
            self.caffemodel_path,
            mean=mean,
            channel_swap=(2,1,0),
            raw_scale=255,
            image_dims=(256, 256))

    def image_labels(self, image):
        input_image = caffe.io.load_image(image)
        prediction = self.classifier.predict([input_image]) 
        return self.class_labels[prediction[0].argmax()]


class FaceDector(object):
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(os.path.join(settings.DATA_ROOT, 'opencv/haarcascades/haarcascade_frontalface_default.xml'))
        self.face_profile_cascade = cv2.CascadeClassifier(os.path.join(settings.DATA_ROOT, 'opencv/haarcascades/haarcascade_profileface.xml'))

    def detect(self, image_path):
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        gray = clahe.apply(gray)

        def item_doc(x, y, w, h):
            return {
                'rect': (int(x), int(y), int(w), int(h)),
            }

        face_docs = [item_doc(x, y, w, h) for x, y, w, h in self.face_cascade.detectMultiScale(gray, 1.3, 5)]
        face_profile_docs = [item_doc(x, y, w, h) for x, y, w, h in self.face_profile_cascade.detectMultiScale(gray, 1.3, 5)]
        faces = face_docs + face_profile_docs

        if len(faces):
            print('Writing Face Detection Images {}'.format(image_path))
            basename, ext = os.path.splitext(image_path)
            for i, f in enumerate(faces):
                x, y, w, h = f['rect']
                ws = 1.0
                hs = 1.10
                wd = int(w * ws)
                hd = int(h * hs)
                x -= wd / 2
                y -= hd / 2
                h += hd
                w = h
                x = max(x, 0)
                y = max(y, 0)
                img_height, img_width = img.shape[:2]
                w = min(img_height, w)
                h = min(img_height, h)
                f['rect'] = (x, y, w, h)

                faceimg = img[y:y+h, x:x+w]
                faceimg_path = '{}-{}{}'.format(basename, i, ext)
                cv2.imwrite(faceimg_path, faceimg)
                directory, filename = os.path.split(faceimg_path)
                f['image_filename'] = filename
                f['image_path'] = faceimg_path

        result = {}
        if len(faces):
            result['faces'] = faces

        return result


class ProcessVideoMgr(BaseCommand):
    def __init__(self, url):
        self.url = url
        self.entity, created = Entity.objects.get_or_create(url=self.url, parent__isnull=True)

    def run_get_youtube_video_info(self):
        oembed = requests.get('https://youtube.com/oembed', params={'url': self.url})
        doc = oembed.json()
        self.entity.type = 'video'
        self.entity.doc = doc
        self.entity.image_url = doc['thumbnail_url'] if doc['thumbnail_url'] else None
        self.entity.title = doc['title'] if doc['title'] else None
        self.entity.save()

    def run_download_video(self):
        yt = YouTube(self.url)
        self.entity.make_storage_root()

        def get_video():
            for ext in ('mp4', 'webem', '3gp', 'flv'):
                _videos = yt.filter(ext)
                if _videos:
                    return _videos[0]

        video = get_video()
        if video:
            self.entity.key = 'video.{}'.format(video.extension)
            self.entity.save()
            if not os.path.isfile(self.entity.video_path):
                video.download(self.entity.video_path)
            return True
        return False

    def run_video_to_images(self):
        """
        ffmpeg -i "$1" -filter:v fps=1,tile=1x1,scale=255:255 "$2/tile%4d.jpg"
        """
        if not os.path.isfile(self.entity.video_path):
            raise Exception('video file not found {}'.format(self.entity.video_path))

        frame_dir = os.path.join(self.entity.storage_root, 'frames')
        if os.path.exists(frame_dir):
            shutil.rmtree(frame_dir)
        os.makedirs(frame_dir)

        video_path = os.path.join(self.entity.storage_root, self.entity.key)

        ffmpeg_cmd_tile = [
            'ffmpeg', '-i', video_path,
            '-filter:v', 'fps=1,tile=1x1',
            os.path.join(frame_dir, '%5d.jpg')
        ]
        run_with_io_timeout(ffmpeg_cmd_tile, timeout_sec=600)

        Entity.objects.filter(parent=self.entity).delete()

        images = glob.glob(os.path.join(frame_dir, '*.jpg'))
        images.sort()

        frames_baseurl = u'{}/frames'.format(self.entity.entity_baseurl)

        for path in images:
            basepath, basename = os.path.split(path)
            url = '{}/{}'.format(frames_baseurl, basename)
            print url
            f, created = Entity.objects.get_or_create(url=url, parent=self.entity)
            f.type = 'image'
            f.title = basename
            f.key = 'frames/{}'.format(basename)
            f.doc = None
            f.save()

    def run_tag_video(self, p_min=0.7):
        ## Caffe image classification models
        image_model = ImageModel.new_image_model('bvlc_googlenet')
        gender_model = FaceGenderAgeImageModel.new_image_model('gender')
        age_model = FaceGenderAgeImageModel.new_image_model('age')

        ## OpenCV HAAR cascade detectors
        face_detector = FaceDector()

        image_qs = Entity.objects.filter(parent=self.entity).order_by('created')
        for image_entity in image_qs:
            image_path = os.path.join(self.entity.storage_root, image_entity.key)
            print(image_path)

            ## initalize feature doc
            image_entity.doc = {}

            ## GoogleNet catagories
            labels = filter(lambda x: x[0] >= p_min, image_model.image_labels(image_path))
            if labels:
                image_entity.doc['bvlc_googlenet'] = labels

            ## faces
            detect_doc = face_detector.detect(image_path)
            if 'faces' in detect_doc:
                print detect_doc['faces']
                image_entity.doc['faces'] = detect_doc['faces']

                for f in image_entity.doc['faces']:
                    gender_labels = gender_model.image_labels(f['image_path'])
                    f['gender'] = gender_labels
                    age_labels = age_model.image_labels(f['image_path'])
                    f['age'] = age_labels

            ## annotate image with detected rects
            item_rects = image_entity.doc.get('faces', [])
            for item_doc in item_rects:
                x, y, w, h = item_doc['rect']
                img = cv2.imread(image_path)
                cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
                cv2.imwrite(image_path, img)
                item_doc['image_url'] = u'{}/{}/frames/{}'.format(settings.ENTITY_BASEURL, self.entity.id, item_doc['image_filename'])

            ## remove frame from DB if there were no labels
            if image_entity.doc:
                image_entity.save()
            else:
                image_entity.delete()


@app.task(name='pictorlabs.add_video')
def add_video_task(url):
    mgr = ProcessVideoMgr(url)
    mgr.run_get_youtube_video_info()    
    mgr.run_download_video()
    mgr.run_video_to_images()
    mgr.run_tag_video()


