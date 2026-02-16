# Skill: Linux Commands Reference

Category: os
Tags: linux, ubuntu, bash, shell, commands

## Package Management

| Action | Command |
|--------|---------|
| Update package list | `sudo apt update` |
| Upgrade packages | `sudo apt upgrade -y` |
| Install package | `sudo apt install <pkg> -y` |
| Remove package | `sudo apt remove <pkg>` |
| Search packages | `apt search <query>` |
| List installed | `apt list --installed` |
| Python packages | `pip install <pkg>` |

## File Operations

| Action | Command |
|--------|---------|
| Copy file | `cp source dest` |
| Copy directory | `cp -r source dest` |
| Move/rename | `mv source dest` |
| Delete file | `rm file` |
| Delete directory | `rm -rf dir/` |
| Find files | `find /path -name "*.py"` |
| File permissions | `chmod 755 file` |
| Change owner | `chown user:group file` |
| Disk usage | `du -sh dir/` |
| Disk free | `df -h` |

## Process Management

| Action | Command |
|--------|---------|
| List processes | `ps aux` |
| Find process | `ps aux \| grep name` |
| Kill process | `kill -9 PID` |
| Service status | `systemctl status service` |
| Start service | `sudo systemctl start service` |
| Stop service | `sudo systemctl stop service` |
| Service logs | `journalctl -u service -f` |

## Networking

| Action | Command |
|--------|---------|
| HTTP request | `curl -s URL` |
| Download file | `wget URL` |
| Active ports | `ss -tlnp` |
| Network interfaces | `ip a` |
| DNS lookup | `nslookup domain` |
| Firewall status | `sudo ufw status` |
| Allow port | `sudo ufw allow PORT` |

## Docker

| Action | Command |
|--------|---------|
| List containers | `docker ps -a` |
| Container logs | `docker logs -f CONTAINER` |
| Run container | `docker run -d --name NAME IMAGE` |
| Stop container | `docker stop CONTAINER` |
| Remove container | `docker rm CONTAINER` |
| List images | `docker images` |
| Compose up | `docker compose up -d` |
| Compose down | `docker compose down` |
| Compose logs | `docker compose logs -f SERVICE` |

## System Info

| Action | Command |
|--------|---------|
| OS version | `lsb_release -a` |
| Kernel | `uname -r` |
| CPU info | `lscpu` |
| Memory | `free -h` |
| Uptime | `uptime` |
| Current user | `whoami` |

## SSH

| Action | Command |
|--------|---------|
| Connect | `ssh user@host` |
| Copy file to remote | `scp file user@host:/path/` |
| Sync directory | `rsync -avz local/ user@host:/remote/` |
| SSH tunnel | `ssh -L local_port:host:remote_port user@host` |
