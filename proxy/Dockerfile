FROM warno-docker-image
MAINTAINER Chris Brantley

COPY /proxy-deb /opt/proxy-deb

#RUN apt-get install -y nginx vim inotify-tools
RUN echo "Installing Proxy .deb files."
RUN dpkg --install --recursive /opt/proxy-deb

COPY nginx.conf /etc/nginx/nginx.conf
COPY runserver.sh /

RUN chmod a+x /runserver.sh

EXPOSE 80
CMD ["/runserver.sh"]
