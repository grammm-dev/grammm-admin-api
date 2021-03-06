# Configuring the API #
## General aspects ##
### How it works ###
Any YAML file placed in this directory will automatically be added to the configuration.
Files are read in alphabetical order. The parameters are updated using the following rules:
- If no parameter with this name exists, it is added
- If a parameter with this name already exists and
    - both are lists, they are concatenated
    - both are objects, they are merged
    - neither of the previous is true, it is overwritten.

### Required parameters ###

Database configuration is mandatory, otherwise only few endpoints will work. See database section below.

## Available parameters ##
### Logging ###
The Python Logging module can be configured by the `logging` object. The object is forwarded to the `logging.config.dictConfig` function, see the Python documentation for available options.
A formatter named `mi-default` is already provided by the default configuration.

### Database ###
Parameters necessary for database connection can be configured by the `DB` object.
Possible parameters are:
- `user` (`string`): User for database access
- `pass` (`string`): Password for user authentication
- `database` (`string`): Name of the database to connect to
- `host` (`string`, default: `127.0.0.1`): Host the database runs on
- `port` (`int`, default: `3306`): Port the database server runs on

### OpenAPI ###
The behavior of the OpenAPI validation can be configured by the `openapi` object.
Possible parameters are:
- `validateRequest` (`boolean`, default: `true`): Whether Request vaildation is enforced. If set to `true`, an invalid request will generate a HTTP 400 response. If set to `false`, the error will only be logged, but the request will be processed.
- `validateResponse` (`boolean`, default: `true`): Whether response validation is enforced. If set to `true`, an invalid response will be replace by a HTTP 500 response. If set to `false`, the error will only be logged and the invalid response is returned anyway.

### Security ###
Parameters regarding security and authentication can be configured by the `security` object
Possible parameters are:
- `jwtPrivateKeyFile` (`string`, default: `res/jwt-privkey.pem`): Path to the private RSA key file
- `jwtPublicKeyFile` (`string`, default: `res/jwt-pubkey.pem`): Path to the public RSA key file

### Managed Configurations ###
Some configurations can be managed by grammm-admin. Parameters can be configured by the `mconf` object.
Possible parameters:
- `ldapPath` (`string`): Path to the LDAP configuration file

### Options ###
Further parameters can be set in the `options` object:
- `dataPath` (`string`, default: `/usr/share/grammm/common`): Directory where shared resources used by Grammm modules are stored
- `propnames` (`string`, default: `propnames.txt`): File containing the list of named properties, relative to `dataPath`
- `portrait` (`string`, default: `admin/api/portrait.jpg`): File containing the default portrait image, relative to `dataPath`
- `domainStoreRatio` (`int`, default: `10`): Mysterious storage factor for `domain.maxSize`
- `domainPrefix` (`string`, default: `/d-data/`): Prefix used for domain exmdb connections
- `userPrefix` (`string`, default: `/u-data/`): Prefix used for user exmdb connections
- `exmdbHost` (`string`, default: `::1`): Hostname of the exmdb service provider
- `exmdbPort` (`string`, default: `5000`): Port of the exmdb service provider
- `fileUid` (`string` or `int`): If set, change ownership of created files to this user
- `fileGid` (`string` or `int`): If set, change ownership of created files to this group
