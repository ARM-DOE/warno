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

# Set the default command to run when starting the container
CMD ["/usr/pgsql-9.3/bin/postgres", "-D", "/var/lib/pgsql/9.3/data"]#, "-c", "/var/lib/pgsql/9.3/data/pg_hba.conf"]
