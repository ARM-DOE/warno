# Local image
FROM warno-docker-image
# Repository image
# FROM centos:7
MAINTAINER Joseph C. Hardin <joseph.hardin@pnnl.gov>

COPY /src /opt/warno-agent/
COPY entrypoint.sh /


ENV NOTVISIBLE "in users profile"
ENV PATH /vagrant/data_store/data/anaconda/bin:$PATH
ENV PATH=/opt/data/anaconda/bin:$PATH


RUN echo "export VISIBLE=now" >> /etc/profile


EXPOSE 80
EXPOSE 6310

WORKDIR /opt/warno-agent
