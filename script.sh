#!/bin/bash

if [ ! -d "netkit-ng" ]; then
  # se pasta netkit-ng nao existir descomprimir ficheiros
  wget -nc https://github.com/netkit-ng/netkit-ng-core/releases/download/3.0.4/netkit-ng-core-32-3.0.4.tar.bz2
  wget -nc https://github.com/netkit-ng/netkit-ng-build/releases/download/0.1.3/netkit-ng-filesystem-i386-F7.0-0.1.3.tar.bz2
  wget -nc https://github.com/netkit-ng/netkit-ng-build/releases/download/0.1.3/netkit-ng-kernel-i386-K3.2-0.1.3.tar.bz2
  tar -xjSf netkit-ng-core-32-3.0.4.tar.bz2
  tar -xjSf netkit-ng-filesystem-i386-F7.0-0.1.3.tar.bz2
  tar -xjSf netkit-ng-kernel-i386-K3.2-0.1.3.tar.bz2
fi

export NETKIT_HOME=$(pwd)/netkit-ng
export MANPATH=:$NETKIT_HOME/man
export PATH=$NETKIT_HOME/bin:$PATH

cd netkit-ng
OUTPUT=$(./check_configuration.sh);
if echo $OUTPUT | grep -q "failed"; then
    #erro na instalacao do netkit
    echo "$OUTPUT"
    exit
fi



cd ../emulation/
lstart



