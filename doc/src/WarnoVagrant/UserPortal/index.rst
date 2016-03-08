.. _user-portal:

User Portal
===========
The User Portal is responsible for managing web and api access to the stored data.

.. toctree::
    :maxdepth: 2

    instruments
    logs
    sites
    users
    views

Introduction
------------

The User Portal is the access point to any data that has been saved by the :ref:`event-manager`.  The User Portal is
present and running at any active instance of an Event Manager, whether it is a site Event Manager or central Event Manager.

The difference between a site User Portal and a central User Portal is that the Event Manager for the central User Portal
collects data from each :ref:`agent` for all of the instruments, but the site Event Manager only gathers data from a site and passes it along
to the central Event Manager.  As such, the central User Portal will have access to all of the data, but site's User
Portal will be limited to the site's data.

The User Portal is accessible through the browser using the standard HTTP or through other programs connecting to the web API.

Design
------

Although the User Portal accesses the data from its :ref:`event-manager`, it never actually communicates with it directly.
They instead both access the database, so that if one fails it does not block the other one from operating. The User Portal
usually doesn't write to the database, but it does have the ability to create new instruments, sites, users, and to submit
logs for an instrument.

The User Portal has a main 'views.py' section which handles requests that don't really fit into a specific category. It also
glues the application together by connecting all of the Flask blueprints. Each Flask blueprint separates the functionality
of the underlying server into logical components. For example, all functions and requests pertaining to instruments are in
one blueprint, while everything pertaining to sites is in another.

Configuration in the Data Store container gives the User Portal everything it needs to connect with the database properly.

HTTP will soon be switched over to HTTPS, which the NGINX proxy server will automatically handle. A REST API
will allow applications to pull in data from the User Portal without needing to use a browser.
This will allow other programs to display and process the data stored by WARNO.