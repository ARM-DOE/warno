FROM warno-docker-image
MAINTAINER Joseph C. Hardin <joseph.hardin@pnnl.gov>

EXPOSE 80

ENV PATH /vagrant/data_store/data/anaconda/bin:$PATH

COPY /src /opt/warno_event_manager/
COPY entrypoint.sh /

WORKDIR /opt/warno_event_manager

