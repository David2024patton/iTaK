# Skill: Windows/PowerShell Commands Reference

Category: os
Tags: windows, powershell, cmd, commands

## Package Management

| Action | Command |
|--------|---------|
| Search packages | `winget search <query>` |
| Install package | `winget install <pkg>` |
| Upgrade all | `winget upgrade --all` |
| Choco install | `choco install <pkg> -y` |
| Python packages | `pip install <pkg>` |

## File Operations

| Action | Command |
|--------|---------|
| Copy file | `Copy-Item source dest` |
| Copy directory | `Copy-Item -Recurse source dest` |
| Move/rename | `Move-Item source dest` |
| Delete file | `Remove-Item file` |
| Delete directory | `Remove-Item -Recurse -Force dir/` |
| Find files | `Get-ChildItem -Recurse -Filter "*.py"` |
| Disk usage | `Get-ChildItem -Recurse \| Measure-Object -Property Length -Sum` |

## Process Management

| Action | Command |
|--------|---------|
| List processes | `Get-Process` |
| Find process | `Get-Process -Name "name"` |
| Kill process | `Stop-Process -Id PID -Force` |
| Service status | `Get-Service -Name service` |
| Start service | `Start-Service -Name service` |
| Stop service | `Stop-Service -Name service` |

## Networking

| Action | Command |
|--------|---------|
| HTTP request | `Invoke-WebRequest -Uri URL` |
| REST API call | `Invoke-RestMethod -Uri URL` |
| Active ports | `netstat -ano \| findstr LISTENING` |
| Test connection | `Test-NetConnection host -Port port` |
| DNS lookup | `Resolve-DnsName domain` |

## Docker

| Action | Command |
|--------|---------|
| List containers | `docker ps -a` |
| Container logs | `docker logs -f CONTAINER` |
| Compose up | `docker compose up -d` |
| Compose down | `docker compose down` |

## System Info

| Action | Command |
|--------|---------|
| OS version | `Get-ComputerInfo \| Select OsName, OsVersion` |
| CPU info | `Get-WmiObject Win32_Processor` |
| Memory | `Get-CimInstance Win32_OperatingSystem \| Select TotalVisibleMemorySize, FreePhysicalMemory` |
| Disk free | `Get-PSDrive C \| Select Used, Free` |
| Current user | `whoami` |
| Environment var | `$env:PATH` |

## SSH

| Action | Command |
|--------|---------|
| Connect | `ssh user@host` |
| Copy file | `scp file user@host:/path/` |
| Key auth | `ssh -i key.pem user@host` |
