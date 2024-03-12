dockerd-entrypoint.sh &
while ! /usr/local/bin/docker info >/dev/null; do
    echo "docker not running yet. Waiting..." >> /proc/1/fd/1;
    sleep 5;
done;
cd /app && docker-compose up;
