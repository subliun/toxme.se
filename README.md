## You can contact the maintainer of the toxme.io directly.

I can be found on freenode IRC, channel #tox , or you can add me from tox by adding toxmeio@toxme.io .

I can assist you with removing or changing your user account on toxme.io in the event that you forget your toxme.io-generated password.

However, please note that you need to be able to prove the account in question is yours. This means that you need to have access to your old toxid.

I am not a tech support for tox issues. If you have an issue with tox, raise a ticket on github or ask someone on the IRC.

# ToxMe source

ToxMe is a speedy and feature-packed Tox name resolution server.

## Installing:

Quick notes before we get started, ToxMe's source is not required to access and use it in a client. Additionally, it's being written in OS X and ran on Ubuntu, so please correct any odd quirks I might accidentally include.

### OS X
Install homebrew from http://brew.sh

```bash
brew install libsodium python3 git libffi
git clone https://github.com/LittleVulpix/toxme
pip install -r misc/requirements.txt
```

And you should be ready!

### Ubuntu
Note: we use Ubuntu 14.04, but newer releases should work too.

```bash
apt-get install python3 python3-pip libffi-dev build-essential wget git sqlite libtool autotools-dev automake checkinstall check git yasm
git clone https://github.com/jedisct1/libsodium.git
cd libsodium
git checkout tags/1.0.3
./autogen.sh
./configure --prefix=/usr
make check
sudo make install
cd ~
git clone https://github.com/LittleVulpix/toxme
cd toxme
pip3 install -r misc/requirements.txt
```

### Optional:
#### postgres support:
##### OS X
```brew install postgresql```

##### Ubuntu
```apt-get install libpq-dev```

##### All ( For Ubuntu, use pip3 instead of pip )
```pip install psycopg2```


## Getting started:

For most testing and development work you'll need both a config.json and a sqlite3 database.

A sample config.json is provided at misc/config.json

A database can be generated locally by running ```sqlite3 -init misc/structure.sql database.db ""```

Now just run python3 src/main.py and it should start automatically!

## Tips:

If you're testing it locally make sure secure_mode in config.json is marked off (0) otherwise you'll be required to reverse proxy it and use an SSL cert

## Documentation:
- [API reference](/doc/api.md)
- [config options](/doc/config.md)
- [PyToxMe](https://github.com/ToxMe/PyToxMe)
