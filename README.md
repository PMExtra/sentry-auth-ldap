# sentry-auth-ldap

[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/PMExtra/sentry-auth-ldap/publish.yaml)](https://github.com/PMExtra/sentry-auth-ldap/actions)
[![PyPI](https://img.shields.io/pypi/v/sentry-auth-ldap)](https://pypi.org/project/sentry-auth-ldap/)
[![License](https://img.shields.io/pypi/l/sentry-auth-ldap)](https://raw.githubusercontent.com/PMExtra/sentry-auth-ldap/master/LICENSE.txt)

A Django custom authentication backend for [Sentry](https://github.com/getsentry/sentry). This module extends the functionality of [django-auth-ldap](https://github.com/django-auth-ldap/django-auth-ldap) with Sentry specific features.

## Features
* Users created by this backend are managed users. Managed fields are not editable through the Sentry account page.
* Users may be auto-added to an Organization upon creation.

## Prerequisites
* Sentry < 21.9.0 should work with [sentry-ldap-auth==2.9.0](https://github.com/Banno/getsentry-ldap-auth) (which is the upstream project for legacy support)
* 21.9.0 ≤ Sentry < 23.6.0 should work with sentry-auth-ldap==21.9.11
* 23.6.0 ≤ Sentry should work with the latest release

> Since sentry-auth-ldap==24.8.0, we'll strive to ensure backward compatibility.

## Installation
To install, simply add `sentry-auth-ldap` to your *requirements.txt* for your Sentry environment (or `pip install sentry-auth-ldap`).

For container environment, because of the minimal base image, it may miss some dependencies.

You can easily [enhance the image](https://develop.sentry.dev/self-hosted/configuration/#updating-basic-configuration) by `sentry/enhance-image.sh` script (need [getsentry/self-hosted](https://github.com/getsentry/self-hosted) 22.6.0 or higher):

```Shell
#!/bin/bash

requirements=(
'sentry-auth-ldap>=21.9.0'
# You can add other packages here, just like requirements.txt
)

# Install the dependencies of ldap
apt-get update
apt-get install -y --no-install-recommends build-essential libldap2-dev libsasl2-dev

pip install ${requirements[@]}

# Clean up to shrink the image size
apt-get purge -y --auto-remove build-essential
rm -rf /var/lib/apt/lists/*

# Support ldap over tls (ldaps://) protocol
mkdir -p /etc/ldap && echo "TLS_CACERT /etc/ssl/certs/ca-certificates.crt" > /etc/ldap/ldap.conf
```

## Configuration
This module extends the [django-auth-ldap](https://django-auth-ldap.readthedocs.io/en/latest/) and all the options it provides are supported (up to v1.2.x, at least). 

To configure Sentry to use this module, add `sentry_auth_ldap.backend.SentryLdapBackend` to your `AUTHENTICATION_BACKENDS` in your *sentry.conf.py*, like this:

```python
AUTHENTICATION_BACKENDS = AUTHENTICATION_BACKENDS + (
    'sentry_auth_ldap.backend.SentryLdapBackend',
)
```

Then, add any applicable configuration options. Depending on your environment, and especially if you are running Sentry in containers, you might consider using [python-decouple](https://pypi.python.org/pypi/python-decouple) so you can set these options via environment variables.

### sentry-auth-ldap Specific Options

```Python
AUTH_LDAP_SENTRY_DEFAULT_ORGANIZATION = 'your-organization-slug'
```
Auto adds created user to the specified organization (matched by name) if it exists.

> **WARNING**: There is an obsoleted setting named `SENTRY_LDAP_DEFAULT_SENTRY_ORGANIZATION`.
> It's used to set the default organization by display name, which is an unsuitable identifier.

```Python
AUTH_LDAP_SENTRY_ORGANIZATION_ROLE_TYPE = 'member'
```
Role type auto-added users are assigned. Valid values in a default installation of Sentry are 'member', 'admin', 'manager' & 'owner'. However, custom roles can also be added to Sentry, in which case these are also valid.

```Python
AUTH_LDAP_SENTRY_ORGANIZATION_GLOBAL_ACCESS = True
```
Whether auto-created users should be granted global access within the default organization.

```Python
AUTH_LDAP_SENTRY_SUBSCRIBE_BY_DEFAULT = False
```
Whether new users should be subscribed to any new projects by default. Disabling
this is useful for large organizations where a subscription to each project
might be spammy.

```Python
AUTH_LDAP_DEFAULT_EMAIL_DOMAIN = 'example.com'
```
Default domain to append to username as the Sentry user's e-mail address when the LDAP user has no `mail` attribute.

> **WARNING**: There is an obsoleted setting named `AUTH_LDAP_SENTRY_USERNAME_FIELD`.  
> It could be replaced by `AUTH_LDAP_USER_QUERY_FIELD` and `AUTH_LDAP_USER_ATTR_MAP` which django-auth-ldap built-in.

### Sentry Options

```Python
SENTRY_MANAGED_USER_FIELDS = ('email', 'first_name', 'last_name', 'password', )
```

Fields which managed users may not modify through the Sentry accounts view. Applies to all managed accounts.

### Example Configuration

```Python
import ldap
from django_auth_ldap.config import LDAPSearch, GroupOfUniqueNamesType

AUTH_LDAP_SERVER_URI = 'ldap://my.ldapserver.com'
AUTH_LDAP_BIND_DN = ''
AUTH_LDAP_BIND_PASSWORD = ''
AUTH_LDAP_USER_QUERY_FIELD = 'username'

AUTH_LDAP_USER_SEARCH = LDAPSearch(
    'dc=domain,dc=com',
    ldap.SCOPE_SUBTREE,
    '(mail=%(user)s)',
)

AUTH_LDAP_USER_ATTR_MAP = {
    'username': 'uid',
    'name': 'cn',
    'email': 'mail'
}

AUTH_LDAP_MAIL_VERIFIED = True

AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    '',
    ldap.SCOPE_SUBTREE,
    '(objectClass=groupOfUniqueNames)'
)

AUTH_LDAP_GROUP_TYPE = GroupOfUniqueNamesType()
AUTH_LDAP_REQUIRE_GROUP = None
AUTH_LDAP_DENY_GROUP = None
AUTH_LDAP_FIND_GROUP_PERMS = False
AUTH_LDAP_GROUP_CACHE_TIMEOUT = 3600

AUTH_LDAP_SENTRY_DEFAULT_ORGANIZATION = 'your-organization-slug'
AUTH_LDAP_SENTRY_ORGANIZATION_ROLE_TYPE = 'member'
AUTH_LDAP_SENTRY_GROUP_ROLE_MAPPING = {
    'owner': ['sysadmins'],
    'admin': ['devleads'],
    'member': ['developers', 'seniordevelopers']
}
AUTH_LDAP_SENTRY_ORGANIZATION_GLOBAL_ACCESS = True

AUTHENTICATION_BACKENDS = AUTHENTICATION_BACKENDS + (
    'sentry_auth_ldap.backend.SentryLdapBackend',
)

# Optional logging for diagnostics.
LOGGING['disable_existing_loggers'] = False
import logging
logger = logging.getLogger('django_auth_ldap')
logger.setLevel(logging.DEBUG)
```

### Troubleshooting

#### Work with LDAPS protocol (SSL/TLS)

Put the below content into /etc/ldap/ldap.conf, otherwise the certificate won't be trusted.

```plain
TLS_CACERT /etc/ssl/certs/ca-certificates.crt
```

If your certificate was issued by a private CA, you should change the path.

#### Don't use OCSP-Must-Staple certificate (SSL/TLS)

Please don't use [OCSP-Must-Staple](https://oid-info.com/get/1.3.6.1.5.5.7.1.24) certificate with LDAPS.

Some ldap servers (eg. OpenLDAP) don't support stapling OCSP response. So it will cause the handshake failed.
