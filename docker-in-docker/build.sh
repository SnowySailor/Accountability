#/bin/bash

mv ../.dockerignore ../.dockerignore.bak;
cp .dockerignore ../;
docker-compose build "$@";
mv ../.dockerignore.bak ../.dockerignore;
