# vagrant-docker
Example of a multi-service development environment

Companion Blog Post: [http://devbandit.com/2015/05/29/vagrant-and-docker.html](http://devbandit.com/2015/05/29/vagrant-and-docker.html)

## Install

First, install the [vagrant-docker-compose](https://github.com/leighmcculloch/vagrant-docker-compose) and [vagrant-triggers](https://github.com/emyl/vagrant-triggers) plugins (as root).

```bash
vagrant plugin install vagrant-docker-compose
vagrant plugin install vagrant-triggers
```

Then run `vagrant up`.