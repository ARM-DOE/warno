VAGRANTFILE_API_VERSION = "2"

env_var_cmd = ""
if ENV['INSTRUMENT']
  value = ENV['INSTRUMENT']
  env_var_cmd = <<CMD
echo "export INSTRUMENT=#{value}" | tee -a /home/vagrant/.profile
CMD
end

script = <<SCRIPT
#{env_var_cmd}
SCRIPT



Vagrant.configure(2) do |config|

  config.vm.box = "warnobox"
  config.vm.network "private_network", ip: "192.168.50.100"
  config.vm.hostname = "warno"
  config.vm.provider "virtualbox" do |v|
    v.name = "warno"
  end

   config.trigger.after :up do
    run "bash ./db_up.sh"
  end

  config.trigger.before :halt do
    run "bash ./db_save.sh"
  end

  config.vm.provision :shell, inline: "docker load -i /vagrant/warno-docker-image"
  config.vm.provision :docker_compose, yml: "/vagrant/docker-compose.yml", rebuild: true, run: "always"
  config.vm.provision :shell, path: "bootstrap.sh"
end
