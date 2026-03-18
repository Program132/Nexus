FROM kalilinux/kali-rolling

ENV DEBIAN_FRONTEND=noninteractive

RUN echo "deb http://archive-4.kali.org/kali kali-rolling main contrib non-free non-free-firmware" > /etc/apt/sources.list
RUN apt-get update && apt-get install -y --no-install-recommends \
    nmap \
    openvpn \
    wget \
    curl \
    dirb \
    ffuf \
    gobuster \
    default-mysql-client \
    netcat-traditional \
    hashcat \
    john \
    metasploit-framework \
    iputils-ping \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    libssl-dev \
    libffi-dev \
    pipx \
    git \
    feroxbuster \
    dnsutils \
    smbclient \
    impacket-scripts \
    tcpdump \
    net-tools \
    iproute2 \
    tmux \
    rlwrap \
    sudo \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pipx ensurepath
RUN pipx install git+https://github.com/Pennyw0rth/NetExec

ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /workspace

CMD ["tail", "-f", "/dev/null"]