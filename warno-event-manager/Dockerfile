# Local image
# FROM warno-docker-image
# Repository image
FROM ubuntu:14.04
MAINTAINER Joseph C. Hardin <joseph.hardin@pnnl.gov>

COPY /src /opt/warno-event-manager/

# Automatic install from remote
RUN apt-get update
RUN apt-get install -y build-essential python-dev python-pip python-psycopg2
RUN pip install -r /opt/warno-event-manager/requirements.txt
RUN apt-get install -y openssh-server

# Manual local install
# RUN echo "Installing Event Manager .deb files."
# WORKDIR /opt/warno-event-manager
# RUN dpkg --install --recursive warno-event-manager-deb
# RUN echo "Installing Event Manager pip requirements."
# RUN bash wempip_install.sh


RUN mkdir /var/run/sshd
RUN echo 'root:screencast' | chpasswd
RUN sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

RUN /usr/sbin/sshd

EXPOSE 80
EXPOSE 22

WORKDIR /opt/warno-event-manager
