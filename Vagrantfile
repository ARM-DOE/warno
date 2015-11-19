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

  config.vm.define "site" do |site|
    site.vm.network "private_network", ip: "192.168.50.99"
    site.vm.hostname = "site"
    site.vm.network "forwarded_port", guest: 80, host: 8080
    site.vm.provider "virtualbox" do |v|
      v.name = "site"
    end
    site.trigger.after :up do
      run "vagrant ssh site -c 'bash /vagrant/db_up.sh'"
    end

    site.trigger.before :halt do
      run "vagrant ssh site -c 'bash /vagrant/db_save.sh'"
    end

    # libpq5 postgresql-client-9.3 postgresql-client-common

    #Automatic update/install
    site.vm.provision :shell, inline: "sudo apt-get update"
    site.vm.provision :shell, inline: "sudo apt-get install -y postgresql-client-9.3 --fix-missing"
    site.vm.provision :docker
    #Local install
    # config.vm.provision :shell, inline: "docker load -i /vagrant/warno-docker-image"

    site.vm.provision :docker_compose, yml: "/vagrant/docker-compose.yml", rebuild: true, run: "always"
    site.vm.provision :shell, path: "bootstrap.sh"
  end

  config.vm.define "central" do |central|
    central.vm.network "private_network", ip: "192.168.50.100"
    central.vm.hostname = "central"
    central.vm.network "forwarded_port", guest: 80, host: 8080
    central.vm.provider "virtualbox" do |v|
      v.name = "central"
    end
    central.trigger.after :up do
      run "vagrant ssh central -c 'bash /vagrant/db_up.sh'"
    end

    central.trigger.before :halt do
      run "vagrant ssh central -c 'bash /vagrant/db_save.sh'"
    end

    # libpq5 postgresql-client-9.3 postgresql-client-common

    #Automatic update/install
    central.vm.provision :shell, inline: "sudo apt-get update"
    central.vm.provision :shell, inline: "sudo apt-get install -y postgresql-client-9.3 --fix-missing"
    central.vm.provision :docker
    #Local install
    # config.vm.provision :shell, inline: "docker load -i /vagrant/warno-docker-image"

    central.vm.provision :docker_compose, yml: "/vagrant/docker-compose.yml", rebuild: true, run: "always"
    central.vm.provision :shell, path: "bootstrap.sh"
  end

end
