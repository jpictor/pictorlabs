#!/bin/bash
docker stop pictorlabs
docker rm pictorlabs
docker run -d -p 127.0.0.1:9193:9193 --name=pictorlabs pictorlabs:latest
