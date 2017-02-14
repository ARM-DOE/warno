require 'yaml'

VAGRANTFILE_API_VERSION = "2"

env_var_cmd = ""
if ENV['WARNO']
  value = ENV['WARNO']
  env_var_cmd = <<CMD
echo "export WARNO=#{value}" | tee -a /home/vagrant/.profile
CMD
end

script = <<SCRIPT
#{env_var_cmd}
SCRIPT

def convert_to_number(string)
  Integer(string || "")
rescue ArgumentError
  nil
end

# Default CPU and Memory configurations.
VM_CPUS = 1       # Physical CPUs
VM_MEMORY = 2048  # Megabytes

# Loads CPU and Memory configuration from the generic configuration file if parameters exist
# Path is relative to Vagrantfile location
vagrant_root = File.dirname(__FILE__)
yaml_config = YAML.load_file(vagrant_root + '/data_store/data/config.yml')


if yaml_config["vagrant"]
  config_cpus = convert_to_number(yaml_config["vagrant"]["cpus"])
  if config_cpus
    VM_CPUS = config_cpus
  end
  config_memory = convert_to_number(yaml_config["vagrant"]["memory"])
  if config_memory
    VM_MEMORY = config_memory
  end
end

Vagrant.configure(2) do |config|
  ## Custom Local Image ##
  config.vm.box = "warnobox1"

  ## Networking##
  config.vm.network "private_network", ip: "192.168.50.100"
  config.vm.hostname = "warno"
  config.vm.network "forwarded_port", guest: 80, host: 8080
  config.vm.network "forwarded_port", guest: 443, host: 8443
  config.vm.network "forwarded_port", guest: 5432, host: 8432
  config.vm.network "forwarded_port", guest: 6379, host: 8379
  config.vm.network "forwarded_port", guest: 6304, host: 6304
  config.vm.network "forwarded_port", guest: 6306, host: 6306
  config.vm.network "forwarded_port", guest: 22, host: 8022, id: "ssh", auto_correct: true

  ## VirtualBox ##
  config.vm.provider "virtualbox" do |v|
    v.name = "warno"
    v.memory = VM_MEMORY   # Megabytes
    v.cpus = VM_CPUS       # Physical CPUs
  end

  ## Set up NFS shared folders ##
  # First disable the CentOS default RSYNC one way synchronization, 
  # then configure NFS two way
  config.vm.synced_folder ".", "/home/vagrant/sync", disabled: true
  config.vm.synced_folder "./", "/vagrant/", type: "nfs"

  # Disable SELinux
  config.vm.provision :shell, inline: "setenforce 0", run: "always"

  ## Load Keys ##
  config.vm.provision :shell, path: "utility_setup_scripts/load_keys.sh", privileged: false, run: "always"

  ## Git Submodule ##
  config.vm.provision :shell, inline: "yum install -y git"
  config.vm.provision :shell, inline: "cd /vagrant && git submodule update --init --recursive", run: "always"

  ## Halt Trigger ##
  config.trigger.before [:halt, :reload] do
    run "vagrant ssh -c 'bash /vagrant/data_store/data/db_save.sh'"
  end

  ## Prerequisite for pip_bootstrap (due to flask-user) ##
  config.vm.provision :shell, inline: "yum install -y libffi-devel"

  ## Final Provisioning ##
  # Must be unprivileged so Anaconda paths install for the vagrant user
  config.vm.provision :shell, path: "utility_setup_scripts/bootstrap.sh", privileged: false
  # Pip installations must be run in a separate bootstrap script, reason unknown
  config.vm.provision :shell, path: "utility_setup_scripts/pip_bootstrap.sh", privileged: false
  
  # Add crontab for regular database backup (currently once daily)
  config.vm.provision :shell, inline: "(crontab -l; echo '0 22 * * * bash /vagrant/data_store/data/db_save.sh') | crontab -"

  # Install Redis
  config.vm.provision :shell, path: "utility_setup_scripts/install_redis.sh"

  # Add hosts to /etc/hosts
  config.vm.provision :shell, path: "utility_setup_scripts/add_hosts.sh"

  # Set up and run database
  config.vm.provision :shell, path: "postgres/init_db.sh"
  config.vm.provision :shell, path: "postgres/start_postgres.sh", run: "always"

  # Start proxy server
  config.vm.provision :shell, path: "proxy/start_proxy.sh", run: "always"

  # Start Redis
  config.vm.provision :shell, path: "redis/start_redis.sh", run: "always"

  # Need to call a script to run all the servers.
  config.vm.provision :shell, path: "utility_setup_scripts/start_all_servers.sh", privileged: false, run: "always"

end
