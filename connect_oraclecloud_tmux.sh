#!/bin/bash
# Connect to the Oracle Cloud instance and start or attach to a tmux session.

# SSH connection details
USER="ubuntu"
HOST="159.54.179.141"
KEY_FILE="~/projects/Rosie/ssh-key-2025-10-22.key"

# The -t flag is used to force pseudo-terminal allocation, which is necessary
# for interactive programs like tmux.
# The remote command first sets the TERM variable for Termux compatibility,
# then tries to attach to a tmux session. If that fails, it creates a new one.
ssh -i "$KEY_FILE" -t "$USER@$HOST" "export TERM=xterm-256color; tmux attach || tmux new"
