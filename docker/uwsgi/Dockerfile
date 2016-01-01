FROM ubuntu
MAINTAINER kelledro
RUN \
  apt-get update && \
  apt-get install -y python-dev python-pip gcc && \
  pip install uwsgi
VOLUME /var/www
WORKDIR /var/www
CMD uwsgi --ini checker.ini
