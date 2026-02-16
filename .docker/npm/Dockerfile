FROM node:latest AS base

#USER root

RUN mkdir /usr/src/app
# RUN mkdir /usr/src/app/starteam
#  && chown -R default:root /usr/src/app \
#  && yum -y install python3 \
#  && yum -y clean all --enablerepo='*'
#WORKDIR /usr/src/app
WORKDIR /usr/src/app
# RUN install mkcert
# COPY ./localhost+4.pem /usr/local/share/ca-certificates/mkcert-rootCA.crt
# RUN update-ca-certificates
#USER default

############################################
# Этот этап используется для сборки        #
############################################
FROM base AS build

# copy the app, note .dockerignore
COPY ./frontend/ /usr/src/app

# для соответствия с продом
RUN npm install --loglevel verbose --no-package-lock

# build necessary, even if no static files are needed,
# since it builds the server as well
RUN npm run build

############################################
# Этот этап используется для разработки    #
############################################
FROM base AS dev

EXPOSE 3000

# ADD docker/npm/start.sh /start.sh
# RUN chmod 775 /start.sh

CMD /bin/bash -c "tail -f /dev/null"