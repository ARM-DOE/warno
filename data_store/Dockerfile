# Local image
FROM warno-docker-image
# Repository image
# FROM centos:7
MAINTAINER Joseph C. Hardin

# COPY /postgres-deb /opt/postgres-deb/

# Automatic install from remote
COPY entrypoint.sh /

# Update config to allow remote connections
RUN /usr/pgsql-9.3/bin/postgresql93-setup initdb
RUN echo "host all all 0.0.0.0/0 trust" >> /var/lib/pgsql/9.3/data/pg_hba.conf
RUN echo "listen_addresses='*'" >> /var/lib/pgsql/9.3/data/postgresql.conf

# switch to the postgres user
USER postgres

# Expose the PostgreSQL port
EXPOSE 5432

ENV PGDATA /var/lib/pgsql/9.3/data

# Create root superuser
RUN /usr/pgsql-9.3/bin/pg_ctl start; sleep 5; echo "root"; psql --command "CREATE USER root WITH SUPERUSER PASSWORD 'password';";\
psql --command "CREATE USER warno WITH SUPERUSER PASSWORD 'warno';";\
psql --command "CREATE DATABASE warno;"

ENV PATH /vagrant/data_store/data/anaconda/bin:$PATH

#RUN echo
#RUN echo;echo;ls -la /var/lib/postgresql;echo;echo
#RUN echo;echo;ls -la /var/lib/postgresql/9.3;echo;echo

# Set the default command to run when starting the container
#CMD ["ls", "-la", "/var/lib/postgresql]
#CMD ["bash /entrypoint.sh"]
