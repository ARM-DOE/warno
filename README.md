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
Then, install the [vagrant-docker-compose](https://github.com/leighmcculloch/vagrant-docker-compose) and [vagrant-triggers](https://github.com/emyl/vagrant-triggers) plugins (as root).

```bash
vagrant plugin install vagrant-docker-compose
vagrant plugin install vagrant-triggers
```

## Start Up Configuration

WARNO Vagrant is run with the event manager as either a "site" event manager or a "central" event manager.

<br>
The default setting is as a "site" event manager.  In *warno-event-manager/src/config.yml* set "cf_url" to "http://**your_central_event_manager_ip**/eventmanager/event"

<br>
If you want to run it as a "central" event manager instead, there are a few different configuration files to change with the current version:
- In the main directory, change "DB_ADDRESS" in both "db_up.sh" and "db_save.sh" to "192.168.50.100"
- In both *warno-event-manager/src/config.yml* and warno-user-portal/src/config.yml, change "central: 0" to "central: 1"
- In *warno-event-manager/src/database/utility.py* change the db address at the top and in each of the engine calls to "192.168.50.100"

<br>
If you want to receive data from the agent running in the virtual machine, set "em_url" in *warno-agent/src/config.yml* to "http://**your_event_manager_ip**/eventmanager/event" or to "http://eventmanager/event" if it is in the same Vagrant virtual machine.

## Start Up
Because each of the machines is either a "site" or "central" machine, Vagrant requires that all of its standard commands are followed by the name of the machine that it applies to (vagrant up, ssh, halt, destroy, etc.)

To start up your Vagrant machine, enter either
```bash
vagrant up central
```
or
```bash
vagrant up site
```

Depending on which type of event manager you would like to bring online.

<br>

## Demo Data
If you start up the "central" virtual machine, you may want to initialize the database with some basic information. (This is currently a requirement as some of the basic event types in the database will not load without this.

To load the data with basic information (basic sites, instruments, instrument data, logs, etc.):
```bash
vagrant ssh central
cd /vagrant/warno-event-manager/src/database/
python populate_demo_db.py
```

## User Portal Access
To access the web server from your browser, just enter "http://**ip_of_host_machine**/radar_status"
