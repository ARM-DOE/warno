.. highlight:: bash

Installation
------------

Prerequisites
^^^^^^^^^^^^^

First, install the latest versions of Vagrant and VirtualBox (Installation instructions for each on their respective sites).

https://www.vagrantup.com/
https://www.virtualbox.org/wiki/Downloads

Then, install the `vagrant-triggers <https://github.com/emyl/vagrant-triggers>`_ plugin (may require superuser privileges).

::

   vagrant plugin install vagrant-triggers


Before you Start
^^^^^^^^^^^^^^^^

WARNO now requires whatever platform it is installed on to be running NFSD. You can install this using whatever method
is appropriate to your machine. For CentOS::

   sudo yum install nfs-utils
   sudo systemctl enable nfs-server
   sudo systemctl restart nfs-server

Also, if you are running Vagrant on CentOS, you also must configure your firewalls to allow the nfsd to send and receive traffic::

   sudo firewall-cmd --permanent --add-service nfs
   sudo firewall-cmd --permanent --add-service rpc-bind
   sudo firewall-cmd --permanent --add-service mountd
   sudo firewall-cmd --permanent --add-port=2049/udp
   sudo firewall-cmd --reload

Then, make sure to download the newest VM image. In the main directory::

   bash utility_setup_scripts/set_up_images.sh

After this, you should have everything set up on the host side.

Start Up Configuration
^^^^^^^^^^^^^^^^^^^^^^

WARNO Vagrant is run with the event manager as either a "site"  event manager or a "central" event manager.

WARNO now runs encrypted by SSL between machines.  On the same VM, however, it communicates internally with
standard HTTP requests.

The default setting is as a "site" event manager.  In *data_store/data/config.yml* set "cf_url" to
"https://**your_central_event_manager_ip**/eventmanager/event".  If you want to run it as a "central" event manager
instead, in *data_store/data/config.yml*, change "central: 0" to "central: 1"

If you want to receive data from the agent running in the virtual machine, set "em_url" in *data_store/data/config.yml*
to "https://**your_event_manager_ip**/eventmanager/event" or to "http://eventmanager/event" if it is in the same Vagrant
virtual machine.

If you have a self signed SSL certificate and private certificate key you would like to use on a machine to encrypt
incoming connections, name them *cacert.pem* and *privkey.pem* respectively and place them in *proxy/*

WARNO comes with some basic starter certificates, but these sample certificates will only work properly for
communicating to "localhost".

If you would rather generate new ones, run the bash scripts *gen_ca.sh* and then *gen_certs.sh* in the main directory,
which will generate and place the files.

On any machine that would like to communicate with the certified machine, there are three settings for "cert_verify" in
*data_store/data/config.yml*:

* "False"  Means the machine will not try to verify that the certificate is correct, and will blindly trust it (not safe
  for production).
* "True"  Means the machine will attempt to verify the certificate with a real certificate authority (CA).
* "path/to/cert"  Will look for a copy of the self signed certificate mentioned above to locally verify the connection.

This allows you to manually copy the "rootCA.pem" that was used to generate the certs (either locally if you generated
the certs or copied from where the certs came from) into the data directory to allow for fairly confident verification
without an outside CA.  Currently, setting this to "/vagrant/data_store/data/rootCA.pem" and copying the *rootCA.pem*
from before to *data_store/data/rootCA.pem* allows either the Event Manager or the Agent to access it as needed.

NFS Permissions
^^^^^^^^^^^^^^^

Because Vagrant uses NFS for file syncing, it requires permission to edit NFS exports.  Although it is possible to enter
the sudo password every time, one alternative is to add the following to /etc/sudoers (CentOS 7, other solutions in the
Vagrant documentation for `NFS Permissions <https://www.vagrantup.com/docs/synced-folders/nfs.html>`_).
::

   Cmnd_Alias VAGRANT_EXPORTS_ADD = /usr/bin/tee -a /etc/exports
   Cmnd_Alias VAGRANT_EXPORTS_COPY = /bin/cp /tmp/exports /etc/exports
   Cmnd_Alias VAGRANT_NFSD_CHECK = /etc/init.d/nfs-kernel-server status
   Cmnd_Alias VAGRANT_NFSD_START = /etc/init.d/nfs-kernel-server start
   Cmnd_Alias VAGRANT_NFSD_APPLY = /usr/sbin/exportfs -ar
   Cmnd_Alias VAGRANT_EXPORTS_REMOVE = /bin/sed -r -e * d -ibak /tmp/exports
   %vboxusers ALL=(root) NOPASSWD: VAGRANT_EXPORTS_ADD, VAGRANT_NFSD_CHECK, VAGRANT_NFSD_START, VAGRANT_NFSD_APPLY, VAGRANT_EXPORTS_REMOVE, VAGRANT_EXPORTS_COPY

*"vboxusers" can be replaced with any group name you would like to give the permissions to*

Multiple VM's one one machine
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you wish to start up a second Vagrant VM on the same machine, there are a few hoops to jump through.  For the second
machine, create a copy of the warno-vagrant directory somewhere else, and in that directory:

Vagrantfile:

* Change the ip to 192.168.50.99
* Change the forwarded ports (host to VM) to unused ports
* Change the vm hostname and virtualbox name away from "warno"

data_store/data/config.yml:

* Change 192.168.50.100 to 192.168.50.99

Start Up
^^^^^^^^

There are two versions of this Vagrant machine, production ('pro') and development ('dev'). The production version uses
slightly more resources (cpu/memory).  To use one or the other, for each vagrant command use 'vagrant <command> <version>'.

To start up your Vagrant machine, enter::

   vagrant up pro

To use the development version, replace 'pro' with 'dev'.

Note that occasionally the machine will get stuck at "Mounting NFS shared folders...".

If this is the case, first attempt::

   sudo systemctl restart nfs-server

If that doesn't work, your firewall may be misconfigured, in which case a quick
::

   sudo systemctl stop firewalld

followed by a
::

   sudo systemctl start firewalld

after the VM starts making progress again should remedy the issue.  This is not a permanent solution, however, and you
should attempt to remedy the firewall configuration issues.

If you suspect the machine failed in some way to be properly created, you can recreate it by::

   vagrant destroy pro
   vagrant up pro

*Note that this will destroy the current virtual machine, and any non-persistant data inside*

Demo Data
^^^^^^^^^

WARNO pre-populates some basic sites and users when it loads up.

To demo data with basic information (basic sites, instruments, instrument data, logs, etc.), simply set
"database":"test_db" to 'true' in *data_store/data/config.yml*.

User Portal Access
^^^^^^^^^^^^^^^^^^

To access the web server from your browser, just enter "https://**ip_of_host_machine**"

Valid Columns for graphs
^^^^^^^^^^^^^^^^^^^^^^^^

To update which columns are valid to graph, visit "https://**ip_of_host_machine**/eventmanager".  This will trigger an
update of the valid columns for each instrument to graph. This can take up to a few minutes, and at the
end it will display a page listing how many columns were updated.

