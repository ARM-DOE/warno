Introduction
============

WARNO uses a Vagrant VM to create a uniform environment regardless of what OS it is on, and within that VM
starts and manages multiple Docker containers, each of them providing their own service to the other containers
or to the user.

Current services include:

- Agent: Gathers, processes, and passes information to the Event Manager (localhost or remote)

- Event Manager: Gathers data passed from multiple agents and either passes it to a more comprehensive Event Manager or stores it in database.

- User Portal:  Web server allowing users to either visit the web site to access data or to pull out data through a set of API hooks.

- Postgresql:  A database server.

- Data Store:  The physical location for database files, configuration, tool installations, and more to be shared between containers.

- Proxy:  An NGINX proxy server responsible for determining whether requests should be passed to the User Portal or the Event Manager running within the same VM.
