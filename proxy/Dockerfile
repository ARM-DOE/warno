FROM warno-docker-image
MAINTAINER Joseph C. Hardin

EXPOSE 80

COPY nginx.conf /etc/nginx/nginx.conf
COPY runserver.sh /

RUN chmod a+x /runserver.sh

CMD ["/runserver.sh"]
