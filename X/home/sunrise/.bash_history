ifconfig
sudo dpkg -i nomachine_*.deb
cd ~/Downloads
sudo dpkg -i nomachine_*.deb
wget https://download.nomachine.com/download/8.11/Linux/nomachine_8.11.3_4_amd64.deb
wget https://www.nomachine.com/free/arm/v8/deb/nomachine_latest_arm64.deb -O nomachine_arm64.deb
sudo dpkg -i nomachine_arm64.deb
rm nomachine_arm64.deb
wget --user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)" https://download.nomachine.com/download/9.4/Raspberry/nomachine_9.4.14_1_arm64.deb -O nomachine_arm64.deb
rm nomachine_arm64.deb
cd Downloads
scp nomachine_9.4.14_1_arm64.deb sunrise@172.20.10.13:/home/sunrise/Downloads/
rm ~/Downloads/nomachine*.deb
ls
wget https://download.nomachine.com/download/9.4/Arm/nomachine_9.4.14_1_arm64.debA
ls
sudo dpkg -i ~/nomachine_*.deb
sudo systemctl stop gdm3
sudo systemctl stop lightdm
sudo /usr/NX/bin/nxserver --restart
ifconfig
