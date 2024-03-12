#/bin/bash

mv ../.dockerignore ../.dockerignore.bak;
cp .dockerignore ../;
cd ..;
docker buildx build --platform linux/amd64 --push -t snowsailor/accountability:newest -f ./docker-in-docker/Dockerfile .;
cd docker-in-docker;
mv ../.dockerignore.bak ../.dockerignore;
