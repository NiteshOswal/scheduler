## Setup UTF-8 Charset
```bash
export LC_ALL="en_US.UTF-8"
export LC_CTYPE="en_US.UTF-8"
sudo dpkg-reconfigure locales
```

## Setup Timezone to UTC
```bash
dpkg-configure tzdata
```

## Install all the dockerized components
```bash
# install necessary docker things
docker pull postgres
docker pull redis
# install pip
apt-get install python-pip
pip install --upgrade pip
```
## Application level packages
```bash
# install Flask, redis, hiredis, celery
pip install Flask celery redis hiredis 
pip install celery[redis]
pip install arrow # moment.js for python
sudo apt-get install python-psycopg2
```

## Setup redis config
```bash
mkdir -p /etc/redis/
cd /etc/redis
wget http://download.redis.io/redis-stable/redis.conf
```
Make the changes as, change the `BIND` address to `0.0.0.0`, `requirepass` to `<password>`

## Start the docker containers
```bash
docker run --name redis-instance -v /redis-data:/data -v /etc/redis:/etc/redis -p 127.0.0.1:6379:6739 -d redis redis-server /etc/redis/redis.conf
docker run --name postgres-instance -v /postgres-data:/var/lib/postgresql/data -p 127.0.0.1:5432:5432 -e POSTGRES_PASSWORD=secret -e POSTGRES_USER=default -d postgres
```
## Copy config files
copy all default files into their main config file..

