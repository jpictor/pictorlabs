# pictorlabs port 9193

FROM ubuntu:16.04

ENV APP_DIR /opt/pictorlabs
ENV NVM_DIR /opt/nvm
ENV NODE_VERSION 6.9

COPY . ${APP_DIR}/
WORKDIR ${APP_DIR}

RUN apt-get -y update && apt-get -y install apt-utils && apt-get -y upgrade && apt-get -y install curl
RUN ./ubuntu-requirements.sh

RUN mkdir -p /opt \
    && curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.33.1/install.sh | bash

RUN ls -l /opt

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
