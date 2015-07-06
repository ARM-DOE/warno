FROM ubuntu:14.04
MAINTAINER Joseph C. Hardin <joseph.hardin@pnnl.gov> 

COPY /src /opt/flask-app/

RUN apt-get update
RUN apt-get install -y build-essential python-dev python-pip python-psycopg2

run pip install -r /opt/flask-app/requirements.txt

RUN apt-get install -y openssh-server
RUN cp /etc/ssh/sshd_config /etc/ssh/sshd_config.original
RUN chmod a-w /etc/ssh/sshd_config.original
RUN mkdir /var/run/sshd
#RUN echo 'root:$6$FDMbctTy$8zA2/N/jUd7P3FrKOgrApZqO1mYr5LX0slHJ0eYR6wnsGuvqge0pn4X5euHVvUJ2ztJIVRqM1xVMfAYGzMlD50' | chpasswd -e  
#RUN sed -ri 's/PermitRootLogin without-password/PermitRootLogin yes/g' /etc/ssh/sshd_config
CMD [“/usr/sbin/sshd”, “-D”]



EXPOSE 80
EXPOSE 22

WORKDIR /opt/flask-app
