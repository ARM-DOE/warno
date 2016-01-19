# Local image
FROM warno-docker-image
# Repository image
# FROM centos:7
MAINTAINER Joseph C. Hardin <joseph.hardin@pnnl.gov>

COPY /src /opt/warno-user-portal/
COPY entrypoint.sh /


##RUN mkdir /var/run/sshd
##RUN echo 'root:screencast' | chpasswd
##RUN sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config


##RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
ENV PATH /vagrant/data_store/data/anaconda/bin:$PATH
RUN echo "export VISIBLE=now" >> /etc/profile

##RUN /usr/sbin/sshd


#RUN pip install -r /opt/warno-user-portal/requirements.txt

EXPOSE 80
EXPOSE 22

WORKDIR /opt/warno-user-portal
