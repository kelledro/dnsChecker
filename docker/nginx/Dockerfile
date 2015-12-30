FROM ubuntu
MAINTAINER kelledro
RUN apt-get update && apt-get install -y nginx
RUN wget https://raw.githubusercontent.com/kelledro/dnsChecker/master/docker/nginx/dnschecker.conf /etc/nginx/sites-enabled/
VOLUME /var/www /var/log/nginx
EXPOSE 80

