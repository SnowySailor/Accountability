#!/bin/bash

retry_limit=12
retry_count=0

start_docker() {
    dockerd-entrypoint.sh &
}

check_docker() {
    /usr/local/bin/docker info >/dev/null
}

start_docker

while ! check_docker; do
    echo "docker not running yet. Waiting..." >> /proc/1/fd/1;
    sleep 5;
    retry_count=$((retry_count+1))
    if [ $retry_count -ge $retry_limit ]; then
        echo "Exceeded retry limit. Restarting docker..." >> /proc/1/fd/1;
        retry_count=0
        start_docker
    fi
done

cd /app && docker-compose up
