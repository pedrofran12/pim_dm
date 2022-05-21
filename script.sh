#!/bin/bash

if [ ! -d "emulation/shared/root/pim_dm" ]; then
  # if project does not exist, clone it
  git clone https://github.com/pedrofran12/pim_dm.git emulation/shared/root/pim_dm
fi

cd emulation/
sudo kathara lclean
sudo kathara lstart --privileged

# open terminal of all nodes
for f in *; do
	if [ -d "$f" -a "$f"=~"shared" ]; then
          gnome-terminal -- kathara connect "$f";
	fi
done



for f in $(ls /sys/devices/virtual/net/ | grep "kt"); do
	sudo bash -c "echo 0 > /sys/devices/virtual/net/$f/bridge/multicast_snooping"
done
