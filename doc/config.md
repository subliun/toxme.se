# Config options refrence

config.json is a json based set of options evaluated by main.py that set various properties and options in the sever.

### Database URL
```"database_url": "sqlite:///tox.db"```

A SQL alchemy style connector to the database to use. This can be sqlite, postgres, mssql, etc.

### Registration domain
```"registration_domain": "localhost"```

The domain appended by ToxMe to the end of records (user@localhost for http://localhost/u/user).

### Server port
```"server_port": 8080```

The port ToxMe listens on for http.

### Server address
```"server_addr": "127.0.0.1"```

The IP ToxMe listens on.

`127.0.0.1` prevents outside connections while `0.0.0.0` allows all.

### PID File
```"pid_file": "pidfile.dl"```

Where ToxMe places it's own PID. Useful for daemons.

### Is proxied
```"is_proxied": 1```

Tells ToxMe to resolve a connecting clients IP from a reverse proxies headers.

### suid
```"suid": "toxme"```

The user ToxMe runs as, please ensure it exists.

### Sandboxing
```"sandbox": 1```

Removes API limits for testing.


### Template
```"templates" : "tox"```

The template to use for the web interface.

### Find friends
```"findfriends_enabled" : 1```

Enables friend discovery features.

### Number of workers
```"number_of_workers": 2```

Number of processes to use.
