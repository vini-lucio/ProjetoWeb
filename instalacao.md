# Instalação Python

marcar adicionar PATH

PowerShell como administrador:

```
Get-ExecutionPolicy
Set-ExecutionPolicy AllSigned -Force
```

# GIT

```
git init
git config --global user.name ‘nome’
git config --global user.email ‘email’
git config --global init.defaultBranch main
git add “nome do arquivo ou .”
git commit -m ‘Initial’
git remote add origin chave_ssh_repositorio
git branch -m main
git push origin main
```

## Gerar Chave SSH

`ssh-keygen -f caminho\arquivo_rsa -t rsa -b 4096`

Se Permission denied (publickey)

`git config --global core.sshCommand "'C:\Windows\System32\OpenSSH\ssh.exe'"`

ou gerar chave ssh pelo app do git

## Incluir chave no Git Hub

pegar ssh do repositorio e adicionar:

`git remote add origin chave_repositorio`

# Django

`django-admin startproject nome_projeto .`

Executar servidor teste e migrações se necessario:

```
python manage.py runserver
python manage.py collectstatic
python manage.py makemigrations
python manage.py migrate
```

## Configurações iniciais Django:

```
python manage.py createsuperuser
python manage.py startapp “nome do app”
```

Incluir arquivo url project:

```
from django.conf import settings
from django.conf.urls.static import static
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

Incluir arquivo settings:

```
from dotenv import load_dotenv
import os
load_dotenv(BASE_DIR / 'dotenv_files' / '.env', override=True)
STATIC_ROOT = BASE_DIR / 'static'
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

# Instalação Ubuntu 24 (terminal)

```
sudo apt update
sudo apt upgrade
sudo apt install build-essential gcc make perl dkms curl
sudo apt install git
```

## Instalar GUI Ubuntu Server 24

```
sudo apt install lightdm
sudo apt install ubuntu-desktop
sudo reboot
```

## Login automático Ubuntu 24

1.	Open the Activities overview and start typing System.
2.	Select Settings ▸ System from the results. This will open the System panel.
3.	Select Users to open the panel.
4.	Press Unlock in the top right corner and type in your password when prompted.
5.	If it is a different user account that you want to log into automatically, select the account under Other Users.
6.	Switch the Automatic Login switch to on.

## Configurar SSH Ubuntu

```
sudo apt install ssh
sudo nano /etc/ssh/sshd_config
```

Pesquisar: PasswordA

Descomentar linha # PasswordAuthentication e mudar para “no”

Pesquisar: MaxAuthTries

Descomentar linha # MaxAuthTries e mudar para algum número maior

`sudo systemctl restart ssh`

No computador que fará o acesso (certificar que o usuário tenha a pasta .ssh): 

`ssh-keygen -f C:\Users\"usuario"\.ssh\"nome_app" -t rsa -b 4096`

Abrir o arquivo criado, copiar o conteúdo no seguinte comando no servidor: 

`nano ~/.ssh/authorized_keys`

`sudo systemctl restart ssh`

No computador que fará o acesso:

`ssh “usuario@ip”`

## Instalações iniciais para o servidor Ubuntu

```
sudo apt update -y
sudo apt upgrade -y
sudo apt autoremove -y
sudo apt install build-essential -y
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.12 python3.12-venv -y
sudo apt install nginx -y
sudo apt install certbot python3-certbot-nginx -y
sudo apt install postgresql postgresql-contrib -y
sudo apt install libpq-dev -y
sudo apt install git -y
```

## Configurações iniciais para o servidor Ubuntu Git

```
git config --global user.name 'Seu nome'
git config --global user.email 'seu_email@gmail.com'
git config --global init.defaultBranch main
mkdir ~/"app_repo" ~/"app_app"
cd "app_repo"/
git init --bare
cd ..
cd "app_app"/
git init
git remote add "app_repo" ~/"app_repo"
git add .
git commit -m 'Initial'
```

No computador local: 

```
git remote add "app_rrepo" "usuario"@"ip":~/"app_repo"
git push "app_repo" main
```

Servidor:

```
cd ..
cd "app_app"/
git pull "app_repo" main
```

Arrumar arquivo .env-CHANGEME

# Configurações iniciais para o servidor Ubuntu Postgressql 

Aparentemente vai sempre gravar em minúsculo os nomes e senhas

```
sudo -u postgres psql
postgres=# create role SYSDBA with login superuser createdb createrole password 'senha';
CREATE ROLE
postgres=# create database "app" with owner SYSDBA;
CREATE DATABASE
postgres=# grant all privileges on database "app" to SYSDBA;
GRANT
postgres=# \q
sudo systemctl restart postgresql
```

## Acessar Postgresql pelo pgadmin4 remotamente

Permitir conecções:

`listen_addresses = '*'`

no arquivo:

`/etc/postgresql/”versão”/main/postgresql.conf`

Liberar o host no arquivo 

`/etc/postgresql/”versão”/main/pg_hba.conf`

`sudo systemctl restart postgresql`


# Configurar Django no servidor Ubuntu

```
cd ~/"app_app"
python3.12 -m venv venv
. venv/bin/activate
pip install --upgrade pip
sudo apt install python3-dev libpq-dev -y
pip install -r requirements.txt
pip install gunicorn
python manage.py runserver (para testar, ctrl+C)
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser
```

## Configurar Gunicorn

```
###############################################################################
# Replace
# __GUNICORN_FILE_NAME__ (app) the name of the gunicorn file you want
# __YOUR_USER__ (ubuntu) your user name
# __APP_ROOT_NAME__ (app_app) the folder name of your project
# __WSGI_FOLDER_NAME__ (projeto django project) the folder name where you find a file called wsgi.py
#
###############################################################################
# Criando o arquivo __GUNICORN_FILE_NAME__.socket
sudo nano /etc/systemd/system/__GUNICORN_FILE_NAME__.socket

# Conteúdo do arquivo socket
[Unit]
Description=gunicorn __GUNICORN_FILE_NAME__ socket

[Socket]
ListenStream=/run/__GUNICORN_FILE_NAME__.socket

[Install]
WantedBy=sockets.target

###############################################################################
# Criando o arquivo __GUNICORN_FILE_NAME__.service
sudo nano /etc/systemd/system/__GUNICORN_FILE_NAME__.service

###############################################################################
# Conteúdo do arquivo
[Unit]
Description=Gunicorn daemon (You can change if you want)
Requires=__GUNICORN_FILE_NAME__.socket
After=network.target

[Service]
User=__YOUR_USER__
Group=www-data
Restart=on-failure
# EnvironmentFile=/home/__YOUR_USER__/__APP_ROOT_NAME__/.env
WorkingDirectory=/home/__YOUR_USER__/__APP_ROOT_NAME__
# --error-logfile --enable-stdio-inheritance --log-level and --capture-output
# are all for debugging purposes.
ExecStart=/home/__YOUR_USER__/__APP_ROOT_NAME__/venv/bin/gunicorn \
          --error-logfile /home/__YOUR_USER__/__APP_ROOT_NAME__/gunicorn-error-log \
          --enable-stdio-inheritance \
          --log-level "debug" \
          --capture-output \
          --access-logfile - \
          --workers 6 \
          --bind unix:/run/__GUNICORN_FILE_NAME__.socket \
          --timeout 120 \
          __WSGI_FOLDER_NAME__.wsgi:application

[Install]
WantedBy=multi-user.target

###############################################################################
# Ativando
sudo systemctl start __GUNICORN_FILE_NAME__.socket
sudo systemctl enable __GUNICORN_FILE_NAME__.socket

# Checando
sudo systemctl status __GUNICORN_FILE_NAME__.socket
sudo systemctl status __GUNICORN_FILE_NAME__.service
curl --unix-socket /run/__GUNICORN_FILE_NAME__.socket localhost
sudo systemctl status __GUNICORN_FILE_NAME__

# Restarting
sudo systemctl restart __GUNICORN_FILE_NAME__.service
sudo systemctl restart __GUNICORN_FILE_NAME__.socket
sudo systemctl restart __GUNICORN_FILE_NAME__

# After changing something
sudo systemctl daemon-reload

# Debugging
sudo journalctl -u __GUNICORN_FILE_NAME__.service
sudo journalctl -u __GUNICORN_FILE_NAME__.socket
```

## Configurar Nginx

```
cd /etc/nginx/sites-enabled/
sudo rm -f default
cd ..
cd sites-available/
sudo nano "app"
```

Colar o que está abaixo de server até o final:

```
# https://www.nginx.com/blog/using-free-ssltls-certificates-from-lets-encrypt-with-nginx/
#
# REPLACES
# __YOUR_DOMAIN_OR_IP__ (ip) = Replace with your domain
# __APP_ABSOLUTE_PATH__ (caminho para app_app) = Replace with the path to the folder for the project
# __STATIC_ABSOLUTE_PATH__ (caminho para app_app/static) = Replace with the path to the folder for static files
# __MEDIA_ABSOLUTE_PATH__ (caminho para app_app/media) = Replace with the path to the folder for media files
# __GUNICORN_FILE_NAME__ (app) = Replace with your unix socket name (don't add .socket)
# 
# Set timezone
# List - timedatectl list-timezones
# sudo timedatectl set-timezone America/Sao_Paulo
#
# HTTP
server {
  listen 80;
  listen [::]:80;
  server_name __YOUR_DOMAIN_OR_IP__;

  # Add index.php to the list if you are using PHP
  index index.html index.htm index.nginx-debian.html index.php;
  
  # ATTENTION: __STATIC_ABSOLUTE_PATH__
  location /static {
    autoindex on;
    alias __STATIC_ABSOLUTE_PATH__;
  }

  # ATTENTION: __MEDIA_ABSOLUTE_PATH__ 
  location /media {
    autoindex on;
    alias __MEDIA_ABSOLUTE_PATH__;
  }

  # ATTENTION: __GUNICORN_FILE_NAME__
  location / {
    proxy_pass http://unix:/run/__GUNICORN_FILE_NAME__.socket;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
    proxy_read_timeout 120;
    proxy_connect_timeout 120;
    proxy_send_timeout 120;
  }

  # deny access to .htaccess files, if Apache's document root
  # concurs with nginx's one
  #
  location ~ /\.ht {
    deny all;
  }

  location ~ /\. {
    access_log off;
    log_not_found off;
    deny all;
  }

  gzip on;
  gzip_disable "msie6";

  gzip_comp_level 6;
  gzip_min_length 1100;
  gzip_buffers 4 32k;
  gzip_proxied any;
  gzip_types
    text/plain
    text/css
    text/js
    text/xml
    text/javascript
    application/javascript
    application/x-javascript
    application/json
    application/xml
    application/rss+xml
    image/svg+xml;

  access_log off;
  #access_log  /var/log/nginx/__YOUR_DOMAIN_OR_IP__-access.log;
  error_log   /var/log/nginx/__YOUR_DOMAIN_OR_IP__-error.log;
}
```

```
cd ../sites-enabled/
sudo ln -s /etc/nginx/sites-available/"app"/etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

### Se não carregar os estilos css:

`sudo nano /etc/nginx/nginx.conf`

comentar linha:

`user www-data;`

incluir:

`user "usario administrador";`

```
sudo systemctl restart "app"
sudo systemctl restart nginx
```

### Permitir arquivos maiores no Nginx

`sudo nano /etc/nginx/nginx.conf`

Adicione em http {}: 

`client_max_body_size 30M;`

`sudo systemctl restart nginx`

## Configurar Serviço Django Background Task

```
sudo nano /etc/systemd/system/django-background-tasks.service

# colar no arquivo

[Unit]
Description=Django Background Tasks Processor
After=network.target
[Service]
User="usuario administrador"
WorkingDirectory=/home/"usuario administrador"/"app_app"
ExecStart=/home/"usuario administrador"/"app_app"/venv/bin/python manage.py process_tasks
Restart=always
[Install]
WantedBy=multi-user.target

# iniciar serviço
sudo systemctl daemon-reload
sudo systemctl start django-background-tasks
sudo systemctl enable django-background-tasks
```

## Oracle thick mode no Ubuntu instantclient

Instant Client Installation for Linux x86-64 (64-bit)

For general Instant Client information, see the [Home Page](https://www.oracle.com/database/technologies/instant-client.html).

ODBC users should follow the [ODBC Installation Instructions](https://www.oracle.com/database/technologies/releasenote-odbc-ic.html).

The "Database Client Installation Guide for Linux" chapter on Installing Oracle Instant Client is here.
Instant Client RPMs are also available without click-through from [yum.oracle.com](http://yum.oracle.com/) for [Oracle Linux 9](https://yum.oracle.com/repo/OracleLinux/OL9/oracle/instantclient23/x86_64/index.html) and [Oracle Linux 8](https://yum.oracle.com/repo/OracleLinux/OL8/oracle/instantclient23/x86_64/index.html). Older RPM packages are available for [Oracle Linux 9](https://yum.oracle.com/repo/OracleLinux/OL9/oracle/instantclient23/x86_64/index.html), [Oracle Linux 8](https://yum.oracle.com/repo/OracleLinux/OL8/oracle/instantclient21/x86_64/), [Oracle Linux 7](https://yum.oracle.com/repo/OracleLinux/OL7/oracle/instantclient21/x86_64/) and [Oracle Linux 6](https://yum.oracle.com/repo/OracleLinux/OL6/oracle/instantclient/x86_64/).

Client-server version interoperability is detailed in [Doc ID 207303.1](https://support.oracle.com/epmos/faces/DocumentDisplay?id=207303.1). For example, Oracle Call Interface 19.3 can connect to Oracle Database 11.2 or later. Some tools may have other restrictions.

Installation of ZIP files:

1.	Download the desired Instant Client ZIP files. All installations require a Basic or Basic Light package.

2.	Unzip the packages into a single directory such as /opt/oracle/instantclient_19_3 that is accessible to your application. For example:

```
cd /opt/oracle
unzip instantclient-basic-linux.x64-19.3.0.0.0dbru.zip
```

The various packages install into subdirectories of /usr/lib/oracle, /usr/include/oracle, and /usr/share/oracle.

3.	Prior to version 18.3, create the appropriate links for the version of Instant Client. For example:

```
cd /opt/oracle/instantclient_12_2
ln -s libclntsh.so.12.1 libclntsh.so
ln -s libocci.so.12.1 libocci.so
```

4.	Install the operating system libaio package. This is called libaio1 on some Linux distributions. On Oracle Linux 8 prior to Instant Client 21 you also need the libnsl package.

For example, on Oracle Linux, run:

```
sudo yum install libaio
sudo apt install libaio-dev
sudo apt install libaio1t64
```

https://askubuntu.com/questions/1511776/ubuntu-24-04-php-8-3-oci8-and-libaio-so-1

The package and the library have been renamed in 24.04. The package name now is libaio1t64 and the library is available as libaio.so.1t64, see https://askubuntu.com/a/1512197/31086

As oci8.so still expecting libaio.so.1, creating the following symlink resolves the issue:

`sudo ln -s /usr/lib/x86_64-linux-gnu/libaio.so.1t64 /usr/lib/x86_64-linux-gnu/libaio.so.1`

5.	If Instant Client is the only Oracle Software installed on this system then update the runtime link path, for example:

```
sudo sh -c "echo /opt/oracle/instantclient_19_24 > /etc/ld.so.conf.d/oracle-instantclient.conf"
sudo ldconfig
```

Alternatively, set the LD_LIBRARY_PATH environment variable prior to running applications. For example:

`export LD_LIBRARY_PATH=/opt/oracle/instantclient_19_24:$LD_LIBRARY_PATH`

The variable can optionally be added to configuration files such as ~/.bash_profile and to application configuration files such as /etc/sysconfig/httpd.

6.	If you intend to co-locate optional Oracle configuration files such as tnsnames.ora, sqlnet.ora, ldap.ora, or oraaccess.xml with Instant Client, put them in the network/admin subdirectory. This needs to be created for 12.2 and earlier, for example:

`mkdir -p /opt/oracle/instantclient_12_2/network/admin`

This is the default Oracle configuration directory for applications linked with this Instant Client.

Alternatively, Oracle configuration files can be put in another, accessible directory. Then set the environment variable TNS_ADMIN to that directory name.

7.	To use binaries such as sqlplus from the SQL*Plus package, unzip the package to the same directory as the Basic package and then update your PATH environment variable, for example:

`export PATH=/opt/oracle/instantclient_19_3:$PATH`

8.	Start your application.

# Reiniciar Serviços

```
sudo systemctl daemon-reload
sudo systemctl restart "app"
sudo systemctl restart nginx
sudo systemctl restart django-background-tasks
```