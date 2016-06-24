Introduction
============

WARNO is designed to allow communication and management of data between machines.  It is used primarily for the
acquisition and processing of instrument status information.  An 'Agent' VM uses plugins to process data from an
instrument, generalizes the information, and passes it along to an 'Event Manager'.

The Event Manager then saves the
data locally and passes the information on to a central Event Manager.  The end result of this is that one or more
Agents can gather and process data from their respective instruments and then all nearby agents can pass their information
to one Event Manager.

All of the Event Managers, each managing the messages from one or more Agents, can then pass on their
messages on to the central Event Manager, which will receive, process, and store all of the data from all instruments.
Users can then browse to a 'User Portal' from any VM with an Event Manager to view data or modify they system, such as
submitting an instrument log.
