#!/bin/bash

# Start Xvfb
Xvfb :99 -screen 0 1920x1080x16 &
export DISPLAY=:99

# Execute the command passed to docker run
exec "$@"