FROM warno-docker-image
MAINTAINER Joseph C. Hardin <joseph.hardin@pnnl.gov>

EXPOSE 443

ENV PATH /vagrant/data_store/data/anaconda/bin:$PATH

COPY /src /opt/warno_user_portal/
COPY entrypoint.sh /

WORKDIR /opt/warno_user_portal
