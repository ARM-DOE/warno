# Local image
# FROM warno-docker-image
# Repository image
FROM centos:7
MAINTAINER Joseph C. Hardin <joseph.hardin@pnnl.gov>

COPY /src /opt/warno-agent/
COPY entrypoint.sh /

# RUN sed -i '1s/^/deb http:\/\/mirror.pnl.gov\/ubuntu\/ trusty main universe restricted /' /etc/apt/sources.list
# RUN sed -i '2s/^/deb http:\/\/mirror.pnl.gov\/ubuntu\/ trusty-updates main universe restricted/' /etc/apt/sources.list
# RUN sed -i '3s/^/deb http:\/\/mirror.pnl.gov\/ubuntu\/ trusty-security main universe restricted /' /etc/apt/sources.list
# RUN sed -i '4,90d' /etc/apt/sources.list

# Automatic install from remote
RUN yum update -y
RUN yum groupinstall -y "Development Tools"

# Manual local install
# RUN echo "Installing Agent .deb files."
# WORKDIR /opt/warno-agent
# RUN dpkg --install --recursive warno-agent-deb

#run pip install -r /opt/warno-agent/requirements.txt

ENV NOTVISIBLE "in users profile"
ENV PATH /vagrant/data_store/data/anaconda/bin:$PATH
RUN echo "export VISIBLE=now" >> /etc/profile


EXPOSE 80
EXPOSE 6310

WORKDIR /opt/warno-agent
