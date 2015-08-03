# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|\
  # Reference: https://docs.vagrantup.com.

  config.vm.box = "ubuntu/trusty32"
  config.vm.provision "shell", path: "provision.sh"

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine. In the example below,
  # accessing "localhost:8080" will access port 80 on the guest machine.
  # config.vm.network "forwarded_port", guest: 80, host: 8080

  # Provider-specific configuration so you can fine-tune various
  # backing providers for Vagrant. These expose provider-specific options.
  # Example for VirtualBox:
  #
  config.vm.provider "virtualbox" do |vb|
    # Display the VirtualBox GUI when booting the machine
    #vb.gui = true
  
    # Customize the amount of memory on the VM:
    #vb.memory = "1024"
  end
  #
  # View the documentation for the provider you are using for more
  # information on available options.

end
