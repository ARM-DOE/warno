# Local image
FROM warno-docker-image
# Repository image
# FROM centos:7
MAINTAINER Joseph C. Hardin

COPY nginx.conf /etc/nginx/nginx.conf
COPY runserver.sh /

RUN chmod a+x /runserver.sh

EXPOSE 80
CMD ["/runserver.sh"]
