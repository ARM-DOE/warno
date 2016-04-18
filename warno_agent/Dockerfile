FROM warno-docker-image
MAINTAINER Joseph C. Hardin <joseph.hardin@pnnl.gov>

EXPOSE 80

ENV PATH /vagrant/data_store/data/anaconda/bin:$PATH

ENV PATH=/opt/data/anaconda/bin:$PATH

EXPOSE 6310

COPY entrypoint.sh /

WORKDIR /opt/warno_agent
