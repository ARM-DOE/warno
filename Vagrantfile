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
  
  config.vm.box = "ubuntu/trusty64"
  config.vm.network "private_network", ip: "192.168.50.100"
  config.vm.hostname = "vagrant-docker-example"

  config.vm.provision :shell, inline: "sudo apt-get update"
  config.vm.provision :docker
  config.vm.provision :docker_compose, yml: "/vagrant/docker-compose.yml", rebuild: true, run: "always"

end
