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
  config.vm.box = "ubuntu/trusty64"
  # Local box
  # config.vm.box = "warnobox"

  config.vm.network "private_network", ip: "192.168.50.100"
  config.vm.hostname = "warno"
  config.vm.network "forwarded_port", guest: 80, host: 8080
  config.vm.provider "virtualbox" do |v|
    v.name = "warno"
  end

  # libpq5 postgresql-client-9.3 postgresql-client-common

  #Automatic update/install
  config.vm.provision :shell, inline: "sudo apt-get update"
  config.vm.provision :shell, inline: "sudo apt-get install -y postgresql-client-9.3 --fix-missing"
  config.vm.provision :docker
  #Local install
  # config.vm.provision :shell, inline: "docker load -i /vagrant/warno-docker-image"

  config.vm.provision :docker_compose, yml: "/vagrant/docker-compose.yml", rebuild: true, run: "always"
  config.vm.provision :shell, path: "bootstrap.sh"

end
