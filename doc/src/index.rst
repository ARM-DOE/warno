.. WARNO documentation master file, created by
   sphinx-quickstart on Fri Feb 19 11:22:36 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to WARNO's documentation!
=================================

WARNO (Watchdog for ARM Radar Network and Operations) uses microservices working in concert to monitor and pull metadata from ARM radars across the world,
process the information, and aggregate it in a central location for long term storage and retrieval.

Sponsored by Pacific Northwest National Laboratory, WARNO is designed to keep track of long term diagnostic information
that was previously much less persistent, allowing for historical analysis of diagnostic data rather than just the most
current values.  WARNO also includes tools to make visualization of this data easier and more centralized.

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2

   WarnoIntroduction/index.rst
   WarnoIntroduction/installation
   WarnoIntroduction/tutorial
   WarnoVagrant/index.rst
   indices

.. include:: indices.rst