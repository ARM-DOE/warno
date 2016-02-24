FROM warno-docker-image
MAINTAINER Joseph C. Hardin <joseph.hardin@pnnl.gov>

# Update config to allow remote connections
RUN /usr/pgsql-9.3/bin/postgresql93-setup initdb
RUN echo "host all all 0.0.0.0/0 trust" >> /var/lib/pgsql/9.3/data/pg_hba.conf
RUN echo "listen_addresses='*'" >> /var/lib/pgsql/9.3/data/postgresql.conf

# Switch to the postgres user
USER postgres

# Expose the PostgreSQL port
EXPOSE 5432

ENV PGDATA /var/lib/pgsql/9.3/data

# Set up database
COPY data/db_setup.sh /
COPY data/parse_yaml.sh /
COPY data/config.yml /
COPY data/secrets.yml /
RUN bash db_setup.sh

ENV PATH /vagrant/data_store/data/anaconda/bin:$PATH

COPY entrypoint.sh /
