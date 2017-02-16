# Setup and Startup

## Configuration

To enable or disable persistence in the Redis config file: comment, uncomment or alter the save directives in the 
'SNAPSHOTTING' section. The snapshots will be stored in whatever directory the server is run from (ideally this main
redis folder).

To change the file that Redis logs to, change the 'logging' directive to point to the desired file.

Changes to logging or database persistence require a full restart of the Redis server.

## Starting the Server

To start the server, run 'start_redis.sh'.  It is best to run the command while the current working directory is
this directory.  The Redis database snapshots will be loaded from and saved to the current working directory at the time
of script execution, and using this default 'redis' folder allows for a predictable location that is persistent
throughout parent VM state.

# Redis Database Items

Keep in mind that some of the entries may change in development before this document is changed, so it may not always be up to date.

## Event Codes

The event codes should match the database event codes.  The description of the event
code is usually the attribute name for a 'non special' event, or the table name for a 'special' event.  A 'special' event usually just means it will trigger its own unique save function, for example, instead of just getting and setting one attribute it will set a whole table of attributes (hence why a 'special' event's description is the matching table name).

**KEY**: 'event_code:*value*'  
**VALUE TYPE**: string  
**VALUE**: The description of the event code.

## Non Tabular Attributes

These are usually data attributes that are considered 'non special' events.  They have no table based organization, instead being composed of two equal length lists, one a list of times and the other being a list of data points gathered at that time.  The lists map to each other, so for example the third element of the 'value' list was gathered at the time represented by the third element of the 'time' list.  These elements are ordered from the most recent elements to the oldest elements, with the list lengths being limited by the functionality that saves them.  

This means that the responsibility of adding the newest values to the beginning of the list, defining a maximum length of the list, and trimming off the oldest values when the list is to long belongs solely to the program itself, and none of it is managed by the Redis database itself.

**KEY**: 'instruments:*instrument_id*:*attribute_name*:time'  
**VALUE TYPE**: list  
**EACH VALUE**: String representation in ISO 8601 format of the time the corresponding value was gathered.

**KEY**: 'instruments:*instrument_id*:*attribute_name*:value'  
**VALUE TYPE**: list  
**EACH VALUE**: String representation of value for the attribute gathered at the corresponding time.  This allows for strings, integers, floats, etc.  Any null data
is represented by the string "NULL".

## Tabular Attributes
These are usually data attributes that are considered 'special' events. They are organized in a table-like fashion, with a list of times that corresponds to many attribute lists.  Each entry in each attribute list corresponds with the time list of the same index.  For example, the third element of every attribute's 'value' list corresponds to the third element of the 'time' list.  In keeping with the mimicry of the table, even attributes that don't receive a value at the same time should be given a placeholder 'NULL' string, otherwise the time and attribute lists could become out of sync. 

As with the non tabular attributes, the responsibility of adding the newest values to the beginning of the list, defining a maximum length of the list, and trimming off the oldest values when the list is to long belongs solely to the program itself, and none of it is managed by the Redis database itself.

**KEY**: 'instruments:*instrument_id*:*table_name*:time'  
**VALUE TYPE**: list  
**EACH VALUE**: String representation in ISO 8601 format of the time the corresponding set of values was gathered.

**_FOR EACH ATTRIBUTE IN TABLE_**


**KEY**: 'instruments:*instrument_id*:*table_name*:*attribute_name*:value'  
**VALUE TYPE**: list  
**EACH VALUE**: String representation of value for the attribute gathered at the corresponding time.  This allows for strings, integers, floats, etc.  Any null data
is represented by the string "NULL".