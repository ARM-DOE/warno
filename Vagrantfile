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
  end

  ## Set up NFS shared folders ##
  config.vm.provision :shell, inline: "sudo yum -y update"
  config.vm.provision :shell, inline: "sudo yum -y install nfs-utils nfs-utils-lib"
  config.vm.synced_folder ".", "/home/vagrant/sync", disabled: true
  config.vm.synced_folder "./", "/vagrant/", type: "nfs"

  # libpq5 postgresql-client-9.3 postgresql-client-common

  ## Automatic update/install ##
  config.vm.provision :shell, inline: "sudo yum -y localinstall http://yum.postgresql.org/9.3/redhat/rhel-7-x86_64/pgdg-centos93-9.3-2.noarch.rpm"
  config.vm.provision :shell, inline: "sudo yum install -y postgresql93 wget bzip2"
  # Without this,SELinux on CentOS blocks docker containers from accessing the NFS shared folders
  config.vm.provision :shell, inline: "sudo setenforce 0", run: "always"

  ## Local install ##
  # config.vm.provision :shell, inline: "docker load -i /vagrant/warno-docker-image"

  config.vm.provision :shell, path: "bootstrap.sh"
  config.vm.provision :docker
  config.vm.provision :shell, inline: "sudo groupadd docker"
  config.vm.provision :shell, inline: "sudo gpasswd -a vagrant docker"
  config.vm.provision :docker_compose, yml: "/vagrant/docker-compose.yml", rebuild: true, run: "always", executable: "/usr/bin/docker-compose"


end
