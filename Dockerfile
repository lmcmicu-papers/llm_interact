# This Dockerfile has been tested on a Raspberry Pi 5 running
# Debian GNU/Linux 12 (bookworm) with the following output for the `uname -a` command:
# Linux eilonwy 6.12.47+rpt-rpi-2712 #1 SMP PREEMPT Debian 1:6.12.47-1+rpt1~bookworm (2025-09-16) aarch64 GNU/Linux
#
# If you are using different hardware you should replace 'ollama-linux-arm64.tgz' below with the appropriate
# `.tgz` file from https://github.com/ollama/ollama/releases.
#
# For more on using docker with Ollama see:
# https://docs.ollama.com/linux

FROM debian:bookworm
CMD ["ollama", "serve"]

# Install needed packages
RUN apt-get update && apt-get install -y wget python3 python3-pip sqlite3

# Uncomment one of the below to either download the Ollama archive using wget or copy it from the host:
# COPY ollama-linux-arm64.tgz ./
RUN wget -nv https://github.com/ollama/ollama/releases/download/v0.12.5/ollama-linux-arm64.tgz

# Install Ollama:
RUN tar -C /usr -xzf ollama-linux-arm64.tgz
RUN rm ollama-linux-arm64.tgz

# Install python development packages:
RUN python3 -m pip config set global.break-system-packages true

# Install the Ollama python libraries and hello_world.py
COPY Makefile ./
COPY requirements.txt ./
RUN pip3 install -r requirements.txt