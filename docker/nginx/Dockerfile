FROM ubuntu
MAINTAINER kelledro
RUN \
  apt-get update && \
  apt-get install -y nginx wget && \
  wget https://raw.githubusercontent.com/kelledro/dnsChecker/master/docker/nginx/dnschecker.conf \
    -O /etc/nginx/sites-enabled/dnschecker.conf && \
  echo "\ndaemon off;" >> /etc/nginx/nginx.conf && \
  rm /etc/nginx/sites-enabled/default
VOLUME /var/www /var/log/nginx
EXPOSE 80
CMD service nginx start
