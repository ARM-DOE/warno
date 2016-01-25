FROM warno-docker-image
MAINTAINER Joseph C. Hardin

# Update config to allow remote connections
RUN /usr/pgsql-9.3/bin/postgresql93-setup initdb
RUN echo "host all all 0.0.0.0/0 trust" >> /var/lib/pgsql/9.3/data/pg_hba.conf
RUN echo "listen_addresses='*'" >> /var/lib/pgsql/9.3/data/postgresql.conf

# Switch to the postgres user
USER postgres

# Expose the PostgreSQL port
EXPOSE 5432

ENV PGDATA /var/lib/pgsql/9.3/data

# Create root superuser
RUN /usr/pgsql-9.3/bin/pg_ctl start; sleep 5; echo "root"; psql --command "CREATE USER root WITH SUPERUSER PASSWORD 'password';";\
psql --command "CREATE USER warno WITH SUPERUSER PASSWORD 'warno';";\
psql --command "CREATE DATABASE warno;"

ENV PATH /vagrant/data_store/data/anaconda/bin:$PATH

COPY entrypoint.sh /
