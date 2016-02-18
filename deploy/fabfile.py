from fabric.api import run, put, cd, settings, env
from fabric.contrib.files import exists
from fabric.contrib.console import confirm
import os.path

PREFIX_PATH = os.environ.get('DEPLOY_CONFIG_PATH')

DEFAULT_HOME = "~/warno/"
IMAGE_SCRIPT = "set_up_images.sh"

PRIVATE_KEY = "id_rsa"
PUBLIC_KEY = "id_rsa.pub"

CONFIG_FILENAME = "config.yml"
CONFIG_FILE = DEFAULT_HOME + "warno-vagrant/data_store/data/config.yml"

DUMP_FILENAME = "db_dump.data.gz"
DUMP_FILE = DEFAULT_HOME + "warno-vagrant/data_store/data/db_dump.data.gz"

SECRETS_FILENAME = "secrets.yml"
SECRETS_FILE = DEFAULT_HOME + "warno-vagrant/data_store/data/" + SECRETS_FILENAME
# TODO: String formatting may not be compatible with python 3

if PREFIX_PATH is None:
    print("Failed to get environment variable 'DEPLOY_CONFIG_PATH',\n"
          "which is used to determine where the configuration file\n"
          "directory is located.  Please refer to the documentation.")

## Test Commands ##
def host_type():
    run('uname -s')

def local_files_for(local_prefix=PREFIX_PATH):
    print env.host
    if os.path.isfile(local_prefix + env.host + "/" + CONFIG_FILENAME):
        print("Found host's config.")
    else:
        print("Could not find host's config.")
    if os.path.isfile(local_prefix + env.host + "/" + DUMP_FILENAME):
        print("Found host's database dump.")
    else:
        print("Could not find host's database dump.")
    if os.path.isfile(local_prefix + env.host + "/" + PRIVATE_KEY):
        print("Found host's private key.")
    else:
        print("Could not find host's private key.")
    if os.path.isfile(local_prefix + env.host + "/" + PUBLIC_KEY):
        print("Found host's public key.")
    else:
        print("Could not find host's public key.")
    if os.path.isfile(local_prefix + SECRETS_FILENAME):
        print("Found secrets file.")
    else:
        print("Could not find secrets file.")

def hello(name="world"):
    print("Hello %s!" % name)

## Push Commands ##
# These commands by default push files from whichever directory the command was called from.
def push_config(config=CONFIG_FILENAME, target=CONFIG_FILE, local_prefix=PREFIX_PATH):
    print local_prefix + env.host + "/" + config
    if os.path.isfile(local_prefix + env.host + "/" + config):
        put(local_prefix + env.host + "/" + config, target)
    elif os.path.isfile(local_prefix + config):
        print("No host-specific config found.  Using parent level config.")
        put(local_prefix + config, target)
    else:
        print("No config file found to copy.")

def push_keys(private=PRIVATE_KEY, public=PUBLIC_KEY, dir=DEFAULT_HOME + "warno-vagrant/", local_prefix=PREFIX_PATH):
    # Will only work with pairs of keys, not single keys.
    if os.path.isfile(local_prefix + env.host + "/" + private) and os.path.isfile(local_prefix + env.host + "/" + public):
        put(local_prefix + env.host + "/" + private, dir)
        put(local_prefix + env.host + "/" + public, dir)
    elif os.path.isfile(local_prefix + private) and os.path.isfile(local_prefix + public):
        print("No host-specific key pair found.  Using parent level key pair.")
        put(local_prefix + private, dir)
        put(local_prefix + public, dir)
    else:
        print("No key pair found to copy.")

def push_secrets(secrets=SECRETS_FILENAME, target=SECRETS_FILE, local_prefix=PREFIX_PATH):
    if os.path.isfile(local_prefix + secrets):
        put(local_prefix + secrets, target)
    else:
        print("No secrets file found to copy.")

def push_db_dump(dumpfile=DUMP_FILENAME, target=DUMP_FILE, local_prefix=PREFIX_PATH):
    if os.path.isfile(local_prefix + env.host + "/" + dumpfile):
        put(local_prefix + env.host + "/" + dumpfile, target)
    elif os.path.isfile(local_prefix + dumpfile):
        print("No host-specific database dump file found.  Using parent level database dump file.")
        put(local_prefix + dumpfile, target)
    else:
        print("No zipped database dump found to copy.")


## Vagrant Commands ##
def push_and_replace_database(dir=DEFAULT_HOME + "warno-vagrant", dumpfile=DUMP_FILENAME, dump_target=DUMP_FILE, local_prefix=PREFIX_PATH):
    # The destroy->start combination forces the VM to load the pushed database file rather than initialize a new database
    if os.path.isfile(local_prefix + env.host + "/" + dumpfile) or os.path.isfile(local_prefix + dumpfile):
        push_db_dump(dumpfile, dump_target, local_prefix)
        destroy_application(dir)
        start_application(dir)
    else:
        print("No zipped database dump found to copy.")

def start_application(dir=DEFAULT_HOME + "warno-vagrant/"):
    with cd(dir):
        run("echo 'Starting Application'")
        run("vagrant up")

def stop_application(dir=DEFAULT_HOME + "warno-vagrant/"):
    with cd(dir):
        run("echo 'Halting Application'")
        run("vagrant halt")

def restart_application(dir=DEFAULT_HOME + "warno-vagrant/"):
    with cd(dir):
        run("echo 'Restarting Application'")
        run("vagrant reload")

def destroy_application(dir=DEFAULT_HOME + "warno-vagrant/"):
    with cd(dir):
        run("echo 'Destroying Application VM'")
        run("vagrant destroy -f")

# Purge does not delete the specified directory that warno-vagrant is installed in, because it may be used
# for something else.
# TODO: Perhaps put in a check asking if the user would like to purge the parent directory as well.
def purge_application(dir=DEFAULT_HOME + "warno-vagrant/"):
    # Destroys the VM and removes the application directory and all files
    if confirm("This will destroy not only the application VM, but remove everything in and including '%s'. Do you wish to continue?" % dir, default=False):
        with cd(dir):
            destroy_application(dir)
            with cd(".."):
                run("echo 'Purging Application'")
                run("rm -r warno-vagrant -f")
    else:
        print("No. Cancelling")


def update_application(dir=DEFAULT_HOME,
                       config=CONFIG_FILENAME, config_target=CONFIG_FILE,
                       private=PRIVATE_KEY, public=PUBLIC_KEY,
                       secrets=SECRETS_FILENAME, secrets_target=SECRETS_FILE, local_prefix=PREFIX_PATH):
    # Creates necessary directories if they don't exist, clones the repo if necessary, stops the VM if it is running
    # to preserve the database.  It then pushes any relevant local files and starts up the application.
    if not exists(dir):
        run("mkdir %s" % dir)
        run("echo 'Created New Directory for Application'")

    with cd(dir):
        new_dir = "%s/%s" % (dir, "warno-vagrant")
        if not exists(new_dir):
            run("echo 'Acquiring Application Code'")
            run("git clone %s" % WARNO_REPO)
        with cd(new_dir):
            needs_halt = False
            with settings(warn_only=True):
                if run("vagrant status | grep 'running'").return_code == 0:
                    needs_halt = True
            # If we streamlined this by putting stop_application in the "with settings" block,
            # "warn_only" might be set for stop_application as well, which is undesirable.
            if needs_halt:
                stop_application(new_dir)
            run("echo 'Updating source code'")
            # May eventually want to use a different method than fetch->reset
            run("git fetch")
            run("git reset --hard origin/master")
            run("bash %s" % IMAGE_SCRIPT)
            push_config(config, config_target, local_prefix)
            push_keys(public, private, new_dir, local_prefix)

            push_secrets(secrets, secrets_target, local_prefix)


            start_application(new_dir)
