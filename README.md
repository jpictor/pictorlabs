# Pictor Labs Application

A common problem in data science is the processing of unstructured data, such as text, to to produce some structured representation of the data. While libraries and SaaS REST APIs exist for processing text, there are few resources for processing video in a similar way. The Pictor Labs API ties together OpenCV, Caffe, and Tensorflow with GPU servers to create a video processing pipeline generate a time series of descriptive tags for video. These tags may then be used in conjunction with user log data to better understand what users are watching in your video content.

This web site allows visitors to survey video tagging results on YouTube videos. As new image classifiers, optical charactor recognition, and other types of information extractors are added to the processing pipline these videos will be reprocessed and results updated.

This is a Django based web application which processes video information
and generates a time-series of structured data labels and extracted information
from the video.  The video processing pipline uses various OpenCV HAAR models,
and Caffe neural net models to label features and classify video images.

## Installation Instructions

TODO...

