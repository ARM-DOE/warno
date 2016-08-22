Fabric
------
Fabric allows the manipulation of WARNO vms remotely.

Environment
First, running the Fabric script works best when run from the directory that
fabfile.py is located in.

Second, this Fabric script requires that you set the environment variable
"DEPLOY_CONFIG_PATH" to point to a configuration directory.  The configuration
directory has a top level "secrets.yml" that will be pushed to all hosts, as well
as a sub directory for each host, with the same name as the host.  The path must
end with a trailing "/" or the script may run into parsing errors.

Each directory can have it's own "config.yml", rsa key pair, or zipped database
dump file.  When Fabric executes for a host, it first checks for the host-specific
configuration file, then for a top level default in the main configuration
directory before abandoning.

Syntax
^^^^^^

::

   fab <command>:arg1=val1,arg2=val2 -H <host1>,<host2>


For the vast majority of commands run, it should be fine to use the default values,
simplifying it to::

   fab <command> -H <host>

Current commands
^^^^^^^^^^^^^^^^

* **push_config**:  Pushes a "config.yml" file from the calling directory into WARNO's
  default location for the file.
* **push_keys**:  Pushes a pair of ssh keys, default "id_rsa" and "id_rsa.pub".
* **push_secrets**: Pushes "secrets.yml" in the same fashion as push_config.
* **push_ssl_ca**: Pushes a personal Certificate Authority bundle to the remote host
  if it exists.
* **push_ssl_certs**: Pushes a local ssl certificate and its private key to the
  remote host, if they exist.
* **push_db_dump**: Pushes "db_dump.data.gz" in the same fashion as push_config.
* **start_application**: Starts the Vagrant machine (vagrant up pro).
* **stop_application**: Stops the Vagrant machine (vagrant halt pro).
* **reload_application**: Reloads the Vagrant machine (vagrant reload pro).
* **destroy_application**: Destroys the Vagrant machine (vagrant destroy -f pro).
* **purge_application**: Destroys the Vagrant machine and forcibly removes the
  containing folder and all files.
* **push_and_replace_database**: Calls push_db_dump, then calls destroy_application
  and start_application. This forces the application to reload the database dump
  file as the database.
* **gen_and_push_ssl_certs**: Generates an ssl certificate and its private key from
  the local custom Certificate Authority (CA) if they are not already present in
  the host's directory.  Then pushes the cert and key in the host's directory and
  the local CA file into the remote host.
* **update_application**: The heavy hitter.  If the directory for the application
  does not exist, creates it and moves into it. Then, if the git repository does
  not already exist, clones the git repository into the directory.  If a Vagrant
  machine is already running, it then halts the machine to preserve the database.
  If "config.yml", the ssh keys, or "secrets.yml" exist in the calling directory,
  they are then pushed into the application directory (push_config, push_keys,
  push_secrets). Next it pushes an ssl certificate and its key if they exist, and
  if they don't, it will attempt to generate and push an ssl certificate and its
  key from a local Certificate Authority bundle (gen_and_push_ssl_certs, unless
  certificate generation is explicitly disabled). After everything is in place,
  it then starts the application (start_application).

Default Configuration
^^^^^^^^^^^^^^^^^^^^^

The default configuration is meant to work in tandem with `warno-configuration
<http://overwatch.pnl.gov/schuman/warno-configuration>`_.  The directory structure
is explained on the README.

The Fabric commands are designed to be run from the directory where fabfile.py
is located.

Custom File Paths
^^^^^^^^^^^^^^^^^

You can change the path prefix by setting the environment variable DEPLOY_CONFIG_PATH, pointing to wherever you have
cloned the configuration directory.