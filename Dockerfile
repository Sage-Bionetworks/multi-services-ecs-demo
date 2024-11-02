FROM ubuntu:22.04

# Update the repository sources list and install apache
RUN apt-get update && \
apt-get install -y git unzip apache2 apache2-dev curl && apt-get clean

# Add config for local rev proxy to internal port
COPY proxy.conf /etc/apache2/sites-available/proxy.conf

# Enable modules
RUN a2enmod proxy proxy_http rewrite headers
# Enable proxy site
RUN a2ensite proxy
# Disable default
RUN a2dissite 000-default

CMD ["apachectl", "-D", "FOREGROUND"]
