To re-enable persistence in the Redis config file, uncomment or alter the save directives in the 'SNAPSHOTTING' section.
The snapshots will be stored in this folder by default (because that is where the server is run from).

To change the file that Redis logs to, change the 'logging' directive to point to the desired file.

These changes require a full restart of the Redis server.

To start the server, just run 'start_redis.sh'.  It is best to run the command while the current working directory is
this directory.  The Redis database snapshots will be loaded from and saved to the current working directory at the time
of script execution, and using this default 'redis' folder allows for a predictable location that is persistent
throughout parent VM state.