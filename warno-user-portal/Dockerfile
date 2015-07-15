FROM ubuntu:14.04
MAINTAINER Joseph C. Hardin <joseph.hardin@pnnl.gov> 

COPY /src /opt/warno-user-portal/

RUN apt-get update
RUN apt-get install -y build-essential python-dev python-pip python-psycopg2 curl

run pip install -r /opt/warno-user-portal/requirements.txt

EXPOSE 80
WORKDIR /opt/warno-user-portal/mysite
