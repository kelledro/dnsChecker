FROM ubuntu
MAINTAINER kelledro
RUN \
  apt-get update && \
  apt-get install -y nginx && \
  wget https://raw.githubusercontent.com/kelledro/dnsChecker/master/docker/nginx/dnschecker.conf /etc/nginx/sites-enabled/ && \
  echo "\ndaemon off;" >> /etc/nginx/nginx.conf
VOLUME /var/www /var/log/nginx
EXPOSE 80
CMD service nginx start
