FROM ubuntu
MAINTAINER kelledro
RUN \
  apt-get update && \
  apt-get install -y python-pip && \
  wget https://raw.githubusercontent.com/kelledro/dnsChecker/master/app/checker.py \
    -O /etc/nginx/sites-enabled/dnschecker.conf 
VOLUME /var/www /var/log/nginx
CMD service nginx start
