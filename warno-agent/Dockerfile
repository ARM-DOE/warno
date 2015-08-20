FROM ubuntu:14.04
MAINTAINER Joseph C. Hardin <joseph.hardin@pnnl.gov> 

COPY /src /opt/warno-agent/

RUN apt-get update
RUN apt-get install -y build-essential python-dev python-pip 

run pip install -r /opt/warno-agent/requirements.txt

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile


EXPOSE 80
EXPOSE 6310

WORKDIR /opt/warno-agent
