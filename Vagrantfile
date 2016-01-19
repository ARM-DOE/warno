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



Vagrant.configure(2) do |config|

  config.vm.box = "warnobox1"

  config.vm.network "private_network", ip: "192.168.50.100"
  config.vm.hostname = "warno"
  config.vm.network "forwarded_port", guest: 80, host: 8080
  config.vm.provider "virtualbox" do |v|
    v.name = "warno"
    # CentOS needs more memory than the default, otherwise docker containers
    # may be killed by the kernel
    v.memory = 1024
  end

  ## Set up NFS shared folders ##
  # First disable the CentOS default RSYNC one way synchronization, 
  # then configure NFS two way
  config.vm.synced_folder ".", "/home/vagrant/sync", disabled: true
  config.vm.synced_folder "./", "/vagrant/", type: "nfs"

  # libpq5 postgresql-client-9.3 postgresql-client-common

  # Without this,SELinux on CentOS blocks docker containers from 
  # accessing the NFS shared folders
  config.vm.provision :shell, inline: "setenforce 0", run: "always"
  #config.vm.provision :shell, inline: "git -C /vagrant submodule update --init --recursive"

  ## Local install ##
  config.vm.provision :shell, inline: "docker load -i /vagrant/warno-docker-image"

  ## Final Provisioning ##
  # Docker and Docker compose are installed in the custom vagrant box
  # Must be unprivileged so Anaconda paths install for the vagrant user
  config.vm.provision :shell, path: "bootstrap.sh", privileged: false
  # Because we could not use the docker-compose provisioner, 
  # we instead write the three equivalent commands
  config.vm.provision :shell, inline: "docker-compose -f /vagrant/docker-compose.yml rm", run: "always"
  config.vm.provision :shell, inline: "docker-compose -f /vagrant/docker-compose.yml build", run: "always"
  config.vm.provision :shell, inline: "docker-compose -f /vagrant/docker-compose.yml up -d --timeout 20", run: "always"

end
