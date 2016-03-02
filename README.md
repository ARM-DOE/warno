# ARM WARNO Vagrant
Multi service development environment designed to modularize and generalize the WARNO software architecture for use on any platform.
<br><br>
A Vagrant virtual machine containing multiple Docker containers, with each container providing a specific service: Database, Proxy Server, SSH Daemon, Agent, Event Manager, User Portal.
<br><br>
- **Agent**: Runs plugins to interface directly with the instruments and process the data before sending it to the site's Event Manager.

- **Event Manager**: Receives data from all Agents on site, compiles the data, and communicates with the main facility's Event Manager.  The main Event Manager processes and stores the data from all sites in the Database

- **User Portal**: Flask web application that provides a user interface to process and display the information saved by the main Event Manager.

## Companion Blog Post
[http://devbandit.com/2015/05/29/vagrant-and-docker.html](http://devbandit.com/2015/05/29/vagrant-and-docker.html)

## Installation

First, install the latest versions of Vagrant and VirtualBox (Installation instructions for each on their respective sites.

https://www.vagrantup.com/

https://www.virtualbox.org/wiki/Downloads
<br><br>
Then, install the [vagrant-docker-compose](https://github.com/leighmcculloch/vagrant-docker-compose) and [vagrant-triggers](https://github.com/emyl/vagrant-triggers) plugins (may require superuser privileges).
```bash
vagrant plugin install vagrant-docker-compose
vagrant plugin install vagrant-triggers
```

## Before you Start

WARNO now requires whatever platform it is installed on to be running NFSD. You can install this using whatever method is appropriate to your machine.

<br>
NFS installation for CentOS
```bash
sudo yum install nfs-utils
sudo systemctl enable nfs-server
sudo systemctl restart nfs-server
```

<br>
Also, if you are running Vagrant on CentOS, you also must configure your firewalls to allow the nfsd to send and receive traffic
```bash
sudo firewall-cmd --permanent --add-service nfs
sudo firewall-cmd --permanent --add-service rpc-bind
sudo firewall-cmd --permanent --add-service mountd
sudo firewall-cmd --permanent --add-port=2049/udp
sudo firewall-cmd --reload
```

<br>

Then, make sure to download the newest VM and Docker images. In the main directory:
```bash
bash set_up_images.sh
```

<br>
After this, you should have everything set up on the host side.

<br>

## Start Up Configuration

WARNO Vagrant is run with the event manager as either a "site"  event manager or a "central" event manager.  

WARNO now runs encrypted by SSL between machines.  On the same VM, however, it communicates internally with standard HTTP requests.

<br>
The default setting is as a "site" event manager.  In *data_store/data/config.yml* set "cf_url" to "https://**your_central_event_manager_ip**/eventmanager/event"

If you want to run it as a "central" event manager instead, in *data_store/data/config.yml*, change "central: 0" to "central: 1"

If you want to receive data from the agent running in the virtual machine, set "em_url" in *data_store/data/config.yml* to "https://**your_event_manager_ip**/eventmanager/event" or to "http://eventmanager/event" if it is in the same Vagrant virtual machine.

<br>

If you have a self signed SSL certificate and private certificate key you would like to use on a machine to encrypt incoming 
connections, name them *cacert.pem* and *privkey.pem* respectively and place them in *proxy/*

If you would rather generate new ones, run the bash scripts *gen_ca.sh* and then *gen_certs.sh* in the main directory, 
which will generate and place the files. 

On any machine that would like to communicate with the certified machine, there are three settings for "cert_verify" in 
*data_store/data/config.yml*:
- "False"  Means the machine will not try to verify that the certificate is correct, and will blindly trust it (not safe for production).
- "True"  Means the machine will attempt to verify the certificate with a real certificate authority (CA).
- "container/path/to/cert"  Will look for a copy of the self signed certificate mentioned above to locally verify the connection.  
This allows you to manually copy the "rootCA.pem" that was used to generate the certs (either locally if you generated the certs 
or copied from where the certs came from) into the data directory to allow for fairly confident verification without an outside CA.
Currently, setting this to "/opt/data/rootCA.pem" (path is due to how docker adds the volume) and copying the *rootCA.pem* from 
before to *data_store/data/rootCA.pem* allows either the Event Manager or the Agent to access it as needed.

<br>
## Multiple VM's one one machine
If you wish to start up a second Vagrant VM on the same machine, there are a few hoops to jump through:

For the second machine, create a copy of the warno-vagrant directory somewhere else, and in that directory:

Vagrantfile:
- Change the ip to 192.168.50.99
- Change the vm hostname and virtualbox name away from "warno"
      
data_store/data/config.yml:
- Change 192.168.50.100 to 192.168.50.99

data_store/data/db_save.sh:
- Change 192.168.50.100 to 192.168.50.99

<br>
## Start Up

To start up your Vagrant machine, enter
```bash
vagrant up
```


Note that currently, occasionally the machine will get stuck at "Mounting NFS shared folders...".

If this is the case, first attempt:
```bash
sudo systemctl restart nfs-server
```

If that doesn't work, your firewall may be misconfigured, in which case a quick
```bash
sudo systemctl stop firewalld
```
followed by a
```bash
sudo systemctl start firewalld
```
after the VM starts making progress again should remedy the issue.  This is not a permanent solution, however, and you should attempt to remedy the firewall configuration issues.

<br>

If you suspect the machine failed in some way to be properly created, you can recreate it by:
```bash
vagrant destroy
vagrant up
```

Note that this will destroy the current virtual machine, and any non-persistant data inside.

<br>

## Demo Data

WARNO pre-populates some basic sites and users when it loads up.

<br>
To demo data with basic information (basic sites, instruments, instrument data, logs, etc.), simply set "database":"test_db" to True in *data_store/data/config.yml*

## User Portal Access
To access the web server from your browser, just enter "https://**ip_of_host_machine**"

<br>

## Fabric
Fabric allows the manipulation of WARNO vms remotely.

### Environment
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

### Syntax
```bash
fab <command>:arg1=val1,arg2=val2 -H <host1>,<host2>
```

For the vast majority of commands run, it should be fine to use the default values, 
simplifying it to:
```bash
fab <command> -H <host>
```

### Current commands
- push_config:  pushes a "config.yml" file from the calling directory into WARNO's 
default location for the file
- push_keys:  pushes a pair of ssh keys, default "id_rsa" and "id_rsa.pub"
- push_secrets: pushes "secrets.yml" in the same fashion as push_config
- push_db_dump: pushes "db_dump.data.gz" in the same fashion as push_config
- start_application: starts the Vagrant machine (vagrant up)
- stop_application: stops the Vagrant machine (vagrant halt)
- reload_application: reloads the Vagrant machine (vagrant reload)
- destroy_application: destroys the Vagrant machine (vagrant destroy -f)
- purge_application: destroys the Vagrant machine and forcibly removes the 
containing folder and all files
- push_and_replace_database: callse push_db_dump, then calls destroy_application 
and start_application. This forces the application to reload the database dump 
file as the database
- update_application: the heavy hitter.  If the directory for the application 
does not exist, creates it and moves into it. Then, if the git repository does 
not already exist, clones the git repository into the directory.  If a Vagrant 
machine is already running, it then halts the machine to preserve the database.  
If "config.yml", the ssh keys, or "secrets.yml" exist in the calling directory, 
they are then pushed into the application directory (push_config, push_keys, push_secrets). 
After everything is in place, it then starts the application (start application)

### Default Configuration
The default configuration is meant to work in tandem with [warno-configuration]
(http://overwatch.pnl.gov/schuman/warno-configuration).  The directory structure
is explained on the README.

The Fabric commands are designed to be run from the directory where fabfile.py
is located.

### Custom File Paths

You can change the path prefix in fabfile.py, pointing to wherever you have cloned
the configuration directory.

<br>
