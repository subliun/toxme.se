##Notice: https://github.com/ToxMe/toxme.se is our new source repo
###https://github.com/Tox/toxme.se is depreciated and unmaintained
#ToxMe source

ToxMe is a speedy and feature packed Tox3 DNS discovery server.

##Installing:

Quick notes before we get started, ToxMe's source is not required to access and use it in a client. Additionally, it's being written in OS X and ran on Ubuntu, so please correct any odd quirks I might accidentally include.

###OS X
Install homebrew from http://brew.sh

```brew install libsodium python3 git libffi```

```git clone https://github.com/ToxMe/toxme.se```

```pip install -r misc/requirements.txt```

And you should be ready!

###Ubuntu
Note: we use Ubuntu 14.04

```apt-get install python3 python3-pip libffi-dev build-essential wget git sqlite```

```wget -P /tmp/ https://download.libsodium.org/libsodium/releases/libsodium-1.0.3.tar.gz```

```cd /tmp/```

```tar -xvf libsodium-1.0.3.tar.gz```

```cd libsodium*```

```./configure --prefix=/usr```

```make -j4 && make install```

```cd .. && rm -rf libsodium*```

```cd ~```

```git clone https://github.com/ToxMe/toxme.se```

```pip install -r misc/requirements.txt```

### Optional:
#### postgres support:
#####OS X
```brew install postgresql```

#####Ubuntu
```apt-get install libpq-dev```

#####All
```pip install psycopg2```


##Getting started:

For most testing and development work you'll need both a config.json and a sqlite3 database.

A sample config.json is provided at misc/config.json

A database can be generated locally by running ```sqlite3 -init misc/structure.sql database.db ""```

Now just run python3 src/main.py and it should start automatically!

##Tips:

If you're testing it locally make sure secure_mode in config.json is marked off (0) otherwise you'll be required to reverse proxy it and use an SSL cert

##Documentation:
- [API refrence](/doc/api.md)
- [config options](/doc/config.md)
- [PyToxMe](https://github.com/ToxMe/PyToxMe)
