# Local image
# FROM warno-docker-image
# Repository image
FROM ubuntu:14.04
MAINTAINER Joseph C. Hardin <joseph.hardin@pnnl.gov>

COPY /src /opt/warno-user-portal/

# Automatic install from remote
RUN apt-get update
RUN apt-get install -y build-essential python-dev python-pip python-psycopg2 curl
RUN pip install -r /opt/warno-user-portal/requirements.txt
RUN apt-get install -y openssh-server

# Manual local install
# RUN echo "Installing User Portal .deb files."
# WORKDIR /opt/warno-user-portal
# RUN dpkg --install --recursive warno-user-portal-deb
# RUN echo "Installing User Portal pip requirements."
# RUN bash wuppip_install.sh

RUN mkdir /var/run/sshd
RUN echo 'root:screencast' | chpasswd
RUN sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config


RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

RUN /usr/sbin/sshd


#RUN pip install -r /opt/warno-user-portal/requirements.txt

EXPOSE 80
EXPOSE 22

WORKDIR /opt/warno-user-portal
