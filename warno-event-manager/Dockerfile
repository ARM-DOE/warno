# Local image
# FROM warno-docker-image
# Repository image
FROM ubuntu:14.04
MAINTAINER Joseph C. Hardin <joseph.hardin@pnnl.gov>

COPY /src /opt/warno-event-manager/

# Automatic install from remote

# RUN sed -i '1s/^/deb http:\/\/mirror.pnl.gov\/ubuntu\/ trusty main universe restricted /' /etc/apt/sources.list
# RUN sed -i '2s/^/deb http:\/\/mirror.pnl.gov\/ubuntu\/ trusty-updates main universe restricted/' /etc/apt/sources.list
# RUN sed -i '3s/^/deb http:\/\/mirror.pnl.gov\/ubuntu\/ trusty-security main universe restricted /' /etc/apt/sources.list
# RUN sed -i '4,90d' /etc/apt/sources.list

RUN apt-get update
RUN apt-get install -y build-essential python-dev python-pip python-psycopg2 python-requests
RUN pip install -r /opt/warno-event-manager/requirements.txt
RUN pip install requests --upgrade
RUN apt-get install -y openssh-server

# Manual local install
# RUN echo "Installing Event Manager .deb files."
# WORKDIR /opt/warno-event-manager
# RUN dpkg --install --recursive warno-event-manager-deb
# RUN echo "Installing Event Manager pip requirements."
# RUN bash wempip_install.sh


WORKDIR /opt/warno-event-manager

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
