#!/usr/bin/env bash

# Modsecurity Install based on this tutorial:
# https://www.inmotionhosting.com/support/server/apache/install-modsecurity-apache-module/
# and crs install file:
# https://raw.githubusercontent.com/coreruleset/coreruleset/v3.2/dev/INSTALL

# Bash script format based on:
# https://github.com/x08d/lockdown.sh/blob/master/lockdown.sh

[[ $EUID -ne 0 ]] && echo "This script must be run as root." && exit 1

#set -x #echo on

apt_update() {
	apt update 
	apt upgrade -y
}

fail2ban() {
		apt install fail2ban -y
	}

install_modsec2_module(){
	apt install -y libapache2-mod-security2
	cp /etc/modsecurity/modsecurity.conf-recommended /etc/modsecurity/modsecurity.conf
	sed -i 's/SecRuleEngine DetectionOnly/SecRuleEngine On/' /etc/modsecurity/modsecurity.conf
	systemctl restart apache2
}

install_crs(){
	apt install -y unzip
	wget https://github.com/coreruleset/coreruleset/archive/v3.3.0.zip
	sha1sum v3.3.0.zip | awk '$1!="5c0e339a359fa71a0a9d983b95a33f6ec3cee8b4"{print "WARNING: Error verifiying checksum"}'
	unzip v3.3.0.zip
	#cp coreruleset-3.3.0/crs-setup.conf.example /etc/modsecurity/crs-setup.conf
	#cp -r coreruleset-3.3.0/rules/ /etc/modsecurity/

	systemctl restart apache2
}

install_auditd(){
	apt install -y auditd
	echo "
-a exit,always -F arch=b64 -S execve
-a exit,always -F arch=b32 -S execve
-a exit,always -F arch=b64 -F a0=2 -S socket
-a exit,always -F arch=b64 -F a0=10 -S socket
-a exit,always -F arch=b64 -S connect
" >> /etc/audit/audit.rules
	sed -i -e "s/^\(log_group\s*=\).*$/\1 adm/" /etc/audit/auditd.conf
	chgrp adm /var/log/audit
	systemctl restart auditd
	#service auditd restart
}

chattr_etc(){
	chattr +i /etc/passwd
	chattr +i /etc/shadow
	chattr +i /etc/gshadow
	chattr +i /etc/hosts
	chattr +i /etc/sudoers
	chattr +i /etc/group
	chattr +i /etc/crontab
	chattr +i /bin/false
	chattr +i /usr/sbin/nologin
}

secure_ssh(){
	sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
	sed -i 's/PermitEmptyPasswords yes/PermitEmptyPasswords no/' /etc/ssh/sshd_config
	sed -i 's/X11Forwarding yes/X11Forwarding no/' /etc/ssh/sshd_config
	chattr +i /etc/ssh/sshd_config
	echo "Don't forget to unchattr and peek through sshd_config for anything suspicious!"
}

run() {
	echo ""	
	typeset -f "$1" | tail -n +2
	echo "$2"
	echo "Run the above commands? [y/N]"
	read -r answer
	if [ "$answer" != "${answer#[Yy]}" ] ;then
		$1
	fi
}

run apt_update "Update and upgrade all packages"
run chattr_etc "Lock important files in etc"
run fail2ban "Install fail2ban"
run install_auditd "Install auditd logger"
run install_modsec2_module "Install the Mod Security Apache Module"
#run install_crs "Install the OWASP Core Rule Set"
run secure_ssh "Set stronger parameters for sshd_config?"
