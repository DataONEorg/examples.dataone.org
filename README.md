# examples.dataone.org
Web interface to examples.dataone.org site

Refactored from subversion `example_service_calls`



## Deployment

The server stack is basically:

```
           Internet
              |
          https @ 443
              |
         [apache2.4]
              |
         http @ 8010
              |
      [gunicorn @ 8010]
       [examples wsgi]
          /       \
    [CN API]     [CN Solr]
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
ExecStart=/var/local/examples.dataone.org/venv/bin/gunicorn -c /var/local/examples.dataone.org/source/config/gunicorn.conf d1_examples:app

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
  SSLProxyEngine On
  ...
  ProxyPass / http://127.0.0.1:8010/
  ProxyPassReverse / http://127.0.0.1:8010/
  <Location /metrics>
    AuthType None
    Require all granted
  </Location>
  <Location /rrda/>
		ProxyPass http://localhost:8081/
		ProxyPassReverse http://localhost:8081/
		Order allow,deny
		Allow from all
	</Location>  
</Virtualhost>
```
