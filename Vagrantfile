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

  # Automatic remote box
  config.vm.box = "centos/7"
  # Local box
  # config.vm.box = "warnobox"

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
  config.vm.provision :shell, inline: "yum -y update"
  config.vm.provision :shell, inline: "yum -y install nfs-utils nfs-utils-lib"
  # First disable the CentOS default RSYNC one way synchronization, 
  # then configure NFS two way
  config.vm.synced_folder ".", "/home/vagrant/sync", disabled: true
  config.vm.synced_folder "./", "/vagrant/", type: "nfs"

  # libpq5 postgresql-client-9.3 postgresql-client-common

  ## Automatic update/install ##
  config.vm.provision :shell, inline: "yum -y localinstall http://yum.postgresql.org/9.3/redhat/rhel-7-x86_64/pgdg-centos93-9.3-2.noarch.rpm"
  config.vm.provision :shell, inline: "yum install -y postgresql93 wget bzip2"
  # Without this,SELinux on CentOS blocks docker containers from 
  # accessing the NFS shared folders
  config.vm.provision :shell, inline: "setenforce 0", run: "always"

  ## Halt Trigger ##
  config.trigger.before [:halt, :reload] do
    run "vagrant ssh -c 'bash /vagrant/data_store/data/db_save.sh'"
  end


  ## Local install ##
  # config.vm.provision :shell, inline: "docker load -i /vagrant/warno-docker-image"

  ## Final Provisioning ##
  # Must be unprivileged so Anaconda paths install for the vagrant user
  config.vm.provision :shell, path: "bootstrap.sh", privileged: false
  config.vm.provision :docker
  # Set Docker to start on each startup 
  # (may not be necessary because of docker provisioner)
  # Add vagrant to docker group, preventing the need to 'sudo' every command
  config.vm.provision :shell, inline: "systemctl enable docker.service"
  config.vm.provision :shell, inline: "groupadd docker"
  config.vm.provision :shell, inline: "gpasswd -a vagrant docker"
  config.vm.provision :shell, inline: "systemctl restart docker.service"
  # Manual installation for docker compose.
  # Most recent version fixes an issue with CentOS builds failing
  config.vm.provision :shell, inline: "curl -L https://github.com/docker/compose/releases/download/1.5.2/docker-compose-`uname -s`-`uname -m` > /usr/bin/docker-compose"
  config.vm.provision :shell, inline: "chmod +x /usr/bin/docker-compose"
  # Because we could not use the docker-compose provisioner, 
  # we instead write the three equivalent commands
  config.vm.provision :shell, inline: "docker-compose -f /vagrant/docker-compose.yml rm", run: "always"
  config.vm.provision :shell, inline: "docker-compose -f /vagrant/docker-compose.yml build", run: "always"
  config.vm.provision :shell, inline: "docker-compose -f /vagrant/docker-compose.yml up -d --timeout 20", run: "always"

end
