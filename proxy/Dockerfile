# Local image
# FROM warno-docker-image
# Repository image
FROM ubuntu:14.04
MAINTAINER Chris Brantley

COPY /proxy-deb /opt/proxy-deb

# Automatic install from remote
#RUN sed -i '1s/^/deb http:\/\/mirror.pnl.gov\/ubuntu\/ trusty main universe restricted /' /etc/apt/sources.list
#RUN sed -i '2s/^/deb http:\/\/mirror.pnl.gov\/ubuntu\/ trusty-updates main universe restricted/' /etc/apt/sources.list
#RUN sed -i '3s/^/deb http:\/\/mirror.pnl.gov\/ubuntu\/ trusty-security main universe restricted /' /etc/apt/sources.list

#RUN sed -i '4,90d' /etc/apt/sources.list

RUN apt-get update
RUN apt-get install -y nginx vim inotify-tools

# Manual local install
# RUN echo "Installing Proxy .deb files."
# RUN dpkg --install --recursive /opt/proxy-deb

COPY nginx.conf /etc/nginx/nginx.conf
COPY runserver.sh /

RUN chmod a+x /runserver.sh

EXPOSE 80
CMD ["/runserver.sh"]
