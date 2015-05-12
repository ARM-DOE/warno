VAGRANTFILE_API_VERSION = "2"

require 'yaml'
containers = YAML.load_file('containers.yml')

Vagrant.configure(2) do |config|
  
  config.vm.box = "ubuntu/trusty64"
  config.vm.network "private_network", ip: "192.168.50.100"
  config.vm.hostname = "vagrant-docker-example"

  config.vm.provision "docker" do |d|
    
    containers.each do |container|
      d.build_image "/vagrant#{container['path']}", args: "-t '#{container['name']}'"
      d.run container['name'], cmd: container['cmd'], args: container['args']
    end

  end

end