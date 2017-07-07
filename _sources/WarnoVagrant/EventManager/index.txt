.. _event-manager:

Event Manager
=============
Event Manager service for WARNO.

.. toctree::
    :maxdepth: 2

    warno_event_manager

Introduction
------------

The Event Manager service is designed to take in and manage all of the events from either :ref:`agent` s or site Event Managers.
A common designation is whether and event manager is a 'site' Event Manager or a 'central' Event Manager.  The main
distinction is that the central Event Manager takes in and manages events for all other Event Managers and Agents.  A
site Event Manager is responsible for managing the events of the Agents that communicate with it and forwarding on the
information to the central Event Manager.

The Event Manager is responsible for communicating with the database to save any information that comes to it.  Any saved
information can be accessed by the :ref:`user-portal`.

Design
------
Events are sent and received as JSON packets.  These packets are usually of the form {Event_Code: *code*, Data: {*data*}}.
The event code lets the Event Manager know what type of event it is and what to do with the data.  For example, an
instrument id request might be an event code of 2. When the Event Manager receives this, it knows that the data section
contains a string with the instrument name and that the requesting entity would like to know what the id for the instrument
with that name is.  The requested information is then returned back to the requesting entity as a JSON packet.

For most events, the event transfer will be one way, up the chain from :ref:`agent` to site Event Manager to central Event Manager.
This will mainly be for status information about the instruments and servers.

The Event Manager also saves events that come to it.  This information can be accessed through the :ref:`user-portal`.
Because the Event Manager handles this database work, it is also responsible for initializing and prepping the database
when the WARNO system starts up.

Depending on the configuration in the Data Store directory, the Event Manager can start
up a normal or a test database.  For a normal database, it will attempt to use an existing database.  If none is set up,
it instead initializes the database and fills it with standard values, such as basic event codes and sites.  If the
database is designated as a test database, it instead will wipe the database every time it starts up and fill it with
basic demo data.  This allows for a regular and controlled testing environment.

The Event Manager will also handle a Redis in-memory database as a cache for the most recent data for each instrument.  At one minute
sampling intervals, the Redis database should hold about 2 weeks of values.  The Redis database is started shortly after the
main database finishes setting up its data.

The configuration also will specify if the current event manager is a site Event Manager or a central Event Manager. If it
is a site Event Manager, the configuration will specify the url for the central Event Manager it is to communicate with.
This configuration also gives the Event Manager all of the information it needs to connect to the database.
