# pictorlabs port 9193

FROM ubuntu:16.04

ENV DEBIAN_FRONTEND noninteractive
ENV APP_DIR /opt/pictorlabs
ENV NVM_DIR /opt/nvm
ENV NODE_VERSION 6.9

RUN apt-get -y update \
 && apt-get -y install apt-utils \
 && apt-get -y upgrade \
 && apt-get -y install curl git cmake pkg-config python-dev python-virtualenv \
 libcurl4-openssl-dev libyaml-dev libxml2-dev libxslt1-dev libmysqlclient-dev \
 libjpeg-dev zlib1g-dev python-dev libjpeg-dev libfreetype6-dev zlib1g-dev \
 libatlas-base-dev liblapack-dev gfortran libpq-dev swig libffi-dev libboost-all-dev \
 libprotobuf-dev libleveldb-dev libsnappy-dev libopencv-dev \
 libhdf5-serial-dev protobuf-compiler

#RUN dpkg -i packages/cuda-repo-ubuntu1604_8.0.61-1_amd64.deb
#RUN apt-get -y update
#RUN apt-get -y --allow-unauthenticated install cuda

#RUN cd /opt \
# && git clone https://github.com/BVLC/caffe.git \
# && cd caffe \
# && cp Makefile.config.example Makefile.config \
# && make all \
# && make test \
# && make runtest

RUN mkdir -p /opt \
 && curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.33.1/install.sh | bash

## done setting up image -- now add app

WORKDIR ${APP_DIR}
COPY . ${APP_DIR}/

RUN /bin/bash -c "source ${NVM_DIR}/nvm.sh \
 && nvm install ${NODE_VERSION} \
 && nvm alias default ${NODE_VERSION} \
 && nvm use default \
 && npm install -g bower"

ENV NODE_PATH $NVM_DIR/v$NODE_VERSION/lib/node_modules
ENV PATH      $NVM_DIR/v$NODE_VERSION/bin:$PATH

RUN /bin/bash -c "source ${NVM_DIR}/nvm.sh \
    && ./manage.sh build_all"

EXPOSE 9193
CMD ["./manage.sh", "rungu_prod"]
