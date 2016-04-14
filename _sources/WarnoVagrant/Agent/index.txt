.. _agent:

Agent
=====

Agent service for WARNO.

.. toctree::
    :maxdepth: 2

    Agent

Introduction
------------
The Agent runs a series of plugins, each responsible for either gathering or processing data and returning
it to the Agent.  The agent then passes the data to the :ref:`event-manager`.
The Agent is also responsible to ensure the proper operation of the plugins, and restart them as necessary.

Design
------

The Agent reads in its configuration on start up from the configuration file located in the Data Store container.  This
tells the Agent what url to connect to so it can communicate with the Agent's :ref:`event-manager`.  Also, if the VM is configured
to not start up the Agent, the Agent will exit before any other startup actions are performed.
The Agent communicates with the Event Manager using JSON packets over an HTTP connection.

Upon startup, the Agent gathers a list of all possible plugins.  For each plugin, if it appears to be a valid plugin,
it is added to the list of plugins the Agent will manage.  For each of these plugins, it runs the plugin's 'register'
function, which may involve communicating with the Agent's Event Manager.  After registering, the plugins are each
started, running a subprocess on the plugin's 'run' function.  The Agent will then relay any packets from the plugins to
the Agent's Event Manager, and if the plugin dies, the Agent will restart the plugin.

Module Contents
---------------