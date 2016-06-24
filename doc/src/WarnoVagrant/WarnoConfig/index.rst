WARNO Config
============
Configuration and utility functions to be used throughout the project.

.. toctree::
    :maxdepth: 2

    config
    utility

Introduction
------------

WarnoConfig is used in :ref:`agent`, :ref:`user-portal`, and :ref:`event-manager` for both configuration and utility
functions.  It provides the sqlalchemy models for the database initialization, helper functions to load in configuration
files, enumerators and helper functions used throughout the project, and database helpers to ease loading and
initializing the database.  Some of these helpers have been deprecated in favor of sqlalchemy builtins.

