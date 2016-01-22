# Local image
FROM warno-docker-image
# Repository image
# FROM centos:7
MAINTAINER Joseph C. Hardin <joseph.hardin@pnnl.gov>

COPY /src /opt/warno-event-manager/
COPY entrypoint.sh /


WORKDIR /opt/warno-event-manager

RUN mkdir /var/run/sshd
RUN echo 'root:screencast' | chpasswd
RUN sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
ENV PATH /vagrant/data_store/data/anaconda/bin:$PATH
RUN echo "export VISIBLE=now" >> /etc/profile

RUN /usr/sbin/sshd

EXPOSE 80
EXPOSE 22
