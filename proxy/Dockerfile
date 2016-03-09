FROM warno-docker-image
MAINTAINER Joseph C. Hardin <joseph.hardin@pnnl.gov>

EXPOSE 80

COPY nginx.conf /etc/nginx/nginx.conf
COPY runserver.sh /

RUN chmod a+x /runserver.sh
RUN chmod 711 /var/lib/nginx /var/lib/nginx/tmp

CMD ["/runserver.sh"]
