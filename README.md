# examples.dataone.org
Web interface to examples.dataone.org site

Refactored from subversion `example_service_calls`


## Running locally

With the requirements installed, navigate to the source folder and run:

```
gunicorn d1_examples:app
```

or to use the `gunicorn.conf` file:

```
./run
```


## Deployment

The server stack is basically:

```
           ┌───────┐                                  
           │Browser│──────────── 443  ──────────┐     
           └───────┘                            │     
               │                                │     
              443                               │     
┌──────────────┴────────────────────┐     ┌──────────┐
│          ┌──────┐                 │     │  CN API  │
│          │Apache│                 │     └──────────┘
│          └──────┘                 │           │     
│             ││                    │           │     
│     ┌───────┘└───────┐            │           │     
│    8081             8010          │          443    
│     │                │            │           │     
│  ┌────┐    ┌──────────────────┐   │           │     
│  │RRDA│    │     Gunicorn     │   │           │     
│  └────┘    │ d1_examples:app  │───┼───────────┘     
│            └──────────────────┘   │                 
└───────────────────────────────────┘                 
```

Examples WSGI and Gunicorn require python 3.5+ and are installed in a
virtual environment.

### The virtual environment

Create the installation location and grab the source:

```
cd /var/local
sudo mkdir examples.dataone.org
sudo chgrp -R adm examples.dataone.org
sudo chmod -R g+w examples.dataone.org
cd examples.dataone.org
git clone https://github.com/DataONEorg/examples.dataone.org.git source
mkdir www
sudo chown -R www-data www
sudo ln -s /var/local/examples.dataone.org/source/d1_examples/static www/static
```

Create the virtual environment in a folder called `venv`:

```
virtualenv venv -p /usr/bin/python3
```

Activate the virtual environment:

```
. /var/local/examples.dataone.org/venv/bin/activate
```

To deactivate the virtual environment:
```
deactivate
```

Install the application in the virtual environment, first ensure the virtual
environment is activated, then:

```
cd /var/local/examples.dataone.org/source
pip install -U -e .
```

### Gunicorn Systemd setup

Create the systemd config `/etc/systemd/system/d1-examples.service`:

```
[Unit]
Description=Gunicorn instance serving examples.dataone.org
After=network.target

[Service]
User=www-data
Group=www-data
Restart=on-failure
WorkingDirectory=/var/local/examples.dataone.org
Environment="PATH=/var/local/examples.dataone.org/venv/bin"
ExecStart=/var/local/examples.dataone.org/venv/bin/gunicorn -c /var/local/examples.dataone.org/source/conf/gunicorn.conf d1_examples:app

[Install]
WantedBy=multi-user.target
```

Activate d1-examples.service:
```
sudo systemctl daemon-reload
```

Start the service:
```
sudo systemctl start d1-examples
```

Stop the service:
```
sudo systemctl stop d1-examples
```

Enable the service at boot:
```
sudo systemctl enable d1-examples
```

### Apache configuration

```
<VirtualHost *:443>
  ServerAdmin administrator@dataone.org
  ServerName examples.dataone.org
  DocumentRoot /var/local/examples.dataone.org/www
  AllowEncodedSlashes On
  AllowEncodedSlashes NoDecode
  Header always set Access-Control-Allow-Origin *
  Header always set Access-Control-Allow-Methods "POST, GET, OPTIONS, DELETE, PUT"
  Header always set Access-Control-Allow-Headers "x-requested-with, Content-Type, origin, authorization, accept,  client-security-token"
  <Directory />
    Options Indexes FollowSymLinks
    AllowOverride All
    Require all granted
    Allow from all
  </Directory>
  SSLEngine on
  SSLCertificateKeyFile  /etc/letsencrypt/live/examples.dataone.org/privkey.pem
  SSLCertificateFile  /etc/letsencrypt/live/examples.dataone.org/fullchain.pem
  SSLProxyEngine On
  ProxyRequests Off
  ProxyPass / http://127.0.0.1:8010/
  ProxyPassReverse / http://127.0.0.1:8010/
  # This is an instance of RRDA listening on port 8081 for DNS resolution
  <Location /rrda/>
		ProxyPass http://localhost:8081/
		ProxyPassReverse http://localhost:8081/
		Order allow,deny
		Allow from all
	</Location>  
  LogLevel info ssl:warn
  ErrorLog ${APACHE_LOG_DIR}/examples-error.log
  CustomLog ${APACHE_LOG_DIR}/examples-access.log combined
  <FilesMatch "\.(cgi|shtml|phtml|php)$">
    SSLOptions +StdEnvVars
  </FilesMatch>
  <Directory /usr/lib/cgi-bin>
    SSLOptions +StdEnvVars
  </Directory>
  BrowserMatch "MSIE [2-6]" \
    nokeepalive ssl-unclean-shutdown \
    downgrade-1.0 force-response-1.0
  # MSIE 7 and newer should be able to use keepalive
  BrowserMatch "MSIE [17-9]" ssl-unclean-shutdown
</Virtualhost>
```

### Log Rotation

Configure logrotate to rotate the logfiles:

Create an entry `/etc/logrotate.d/d1-examples`

```
/var/log/d1-examples/*.log {
	monthly
	dateext
  dateformat -%Y-%m
  dateyesterday
  rotate 1000
}
```

Which rotates monthly, has -YEAR-MONTH added to the rotated file names, and 
keeps 1000 log files around.
