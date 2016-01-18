# Local image
# FROM warno-docker-image
# Repository image
FROM centos:7
MAINTAINER Joseph C. Hardin


RUN yum update -y
RUN yum install -y epel-release
RUN yum install -y nginx vim inotify-tools systemd

# Manual local install
# RUN echo "Installing Proxy .deb files."
# RUN dpkg --install --recursive /opt/proxy-deb

COPY nginx.conf /etc/nginx/nginx.conf
COPY runserver.sh /

RUN chmod a+x /runserver.sh

EXPOSE 80
CMD ["/runserver.sh"]
