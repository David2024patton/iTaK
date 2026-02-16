# Skill: macOS Commands Reference

Category: os
Tags: macos, darwin, brew, terminal

## Package Management

| Action | Command |
|--------|---------|
| Install Homebrew | `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"` |
| Install package | `brew install <pkg>` |
| Update packages | `brew update && brew upgrade` |
| Search packages | `brew search <query>` |
| Cask install | `brew install --cask <app>` |
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
| Open in Finder | `open .` |
| Disk usage | `du -sh dir/` |
| Disk free | `df -h` |

## Process Management

| Action | Command |
|--------|---------|
| List processes | `ps aux` |
| Kill process | `kill -9 PID` |
| Activity Monitor | `top` or `htop` |
| Service management | `launchctl list` |
| Check port | `lsof -i :PORT` |

## Networking

| Action | Command |
|--------|---------|
| HTTP request | `curl -s URL` |
| Download file | `wget URL` (requires brew install wget) |
| Active ports | `lsof -i -P -n \| grep LISTEN` |
| Network config | `networksetup -listallhardwareports` |
| DNS lookup | `nslookup domain` |

## System Info

| Action | Command |
|--------|---------|
| OS version | `sw_vers` |
| Kernel | `uname -r` |
| CPU info | `sysctl -n machdep.cpu.brand_string` |
| Memory | `sysctl -n hw.memsize` |
| Current user | `whoami` |
