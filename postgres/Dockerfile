# Local image
# FROM warno-docker-image
# Repository image
FROM centos:7
MAINTAINER Joseph C. Hardin

COPY /postgres-deb /opt/postgres-deb/

# Install PostgreSQL

# Automatic install from remote
RUN yum -y install deltarpm
RUN yum -y localinstall http://yum.postgresql.org/9.3/redhat/rhel-7-x86_64/pgdg-centos93-9.3-2.noarch.rpm
RUN yum install -y postgresql93 postgresql93-contrib postgresql93-server

# Manual local install
# RUN echo "Installing Postgres .deb files."
# RUN dpkg --install --recursive /opt/postgres-deb

# Update config to allow remote connections
RUN /usr/pgsql-9.3/bin/postgresql93-setup initdb
RUN echo "host all all 0.0.0.0/0 trust" >> /var/lib/pgsql/9.3/data/pg_hba.conf
RUN echo "listen_addresses='*'" >> /var/lib/pgsql/9.3/data/postgresql.conf

#RUN echo;echo;ls -la /var/lib/postgresl;echo;echo

# switch to the postgres user
USER postgres

# Expose the PostgreSQL port
EXPOSE 5432

#RUN echo
#RUN echo;echo;ls -la /var/lib/postgresql;echo;echo
#RUN echo;echo;ls -la /var/lib/postgresql/9.3;echo;echo

# Set the default command to run when starting the container
#CMD ["ls", "-la", "/var/lib/postgresql]
CMD ["/usr/pgsql-9.3/bin/postgres", "-D", "/var/lib/pgsql/9.3/data"]#, "-c", "/var/lib/pgsql/9.3/data/pg_hba.conf"]
