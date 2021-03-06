# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2020-2021 grammm GmbH

from . import DB
from tools.constants import PropTags, PropTypes
from tools.rop import ntTime, nxTime
from tools.DataModel import DataModel, Id, Text, Int, Date, BoolP, RefProp
from tools.misc import createMapping

from sqlalchemy import func, ForeignKey
from sqlalchemy.dialects.mysql import INTEGER, TINYINT
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, selectinload
from sqlalchemy.orm.collections import attribute_mapped_collection

import crypt
import re
import time
from base64 import b64decode, b64encode
from datetime import datetime
from ldap3.utils.conv import escape_filter_chars


class Groups(DataModel, DB.Model):
    __tablename__ = "groups"

    ID = DB.Column("id", INTEGER(10, unsigned=True), nullable=False, primary_key=True, unique=True)
    groupname = DB.Column("groupname", DB.VARCHAR(128), nullable=False, unique=True)
    domainID = DB.Column("domain_id", INTEGER(10, unsigned=True), nullable=False, index=True)
    title = DB.Column("title", DB.VARCHAR(128), nullable=False)

    _dictmapping_ = ((Id(), Text("title", flags="patch"), Text("groupname", flags="init")),
                     (Id("domainID", flags="init, hidden"),),
                     ())

    NORMAL = 0
    SUSPEND = 1

    @staticmethod
    def checkCreateParams(data):
        from orm.domains import Domains
        domain = Domains.query.filter(Domains.ID == data.get("domainID")).first()
        if domain is None:
            return "Invalid domain"
        if "groupname" not in data:
            return "Missing required property 'groupname'"
        if "@" not in "groupname":
            data["groupname"] += "@"+domain.domainname
        elif data["groupname"].split("@")[1] != domain.domainname:
            return "Domain specifications mismatch."


class Users(DataModel, DB.Model):
    __tablename__ = "users"

    ID = DB.Column("id", INTEGER(10, unsigned=True), nullable=False, primary_key=True, unique=True)
    username = DB.Column("username", DB.VARCHAR(128), nullable=False, unique=True)
    _password = DB.Column("password", DB.VARCHAR(40), nullable=False, server_default="")
    groupID = DB.Column("group_id", INTEGER(10, unsigned=True), nullable=False, index=True, default=0)
    domainID = DB.Column("domain_id", INTEGER(10, unsigned=True), nullable=False, index=True)
    maildir = DB.Column("maildir", DB.VARCHAR(128), nullable=False, server_default="")
    addressStatus = DB.Column("address_status", TINYINT, nullable=False, server_default="0")
    privilegeBits = DB.Column("privilege_bits", INTEGER(10, unsigned=True), nullable=False, default=0)
    externID = DB.Column("externid", DB.VARBINARY(64))
    _deprecated_maxSize = DB.Column("max_size", INTEGER(10), nullable=False, default=0)
    _deprecated_addressType = DB.Column("address_type", TINYINT, nullable=False, server_default="0")
    _deprecated_subType = DB.Column("sub_type", TINYINT, nullable=False, server_default="0")

    roles = relationship("AdminRoles", secondary="admin_user_role_relation", cascade="all, delete")
    properties = relationship("UserProperties", cascade="all, delete-orphan", single_parent=True,
                              collection_class=attribute_mapped_collection("name"))
    aliases = relationship("Aliases", cascade="all, delete-orphan", single_parent=True)

    _dictmapping_ = ((Id(), Text("username", flags="init")),
                     (Id("domainID", flags="init"),
                      Id("groupID", flags="patch"),
                      {"attr": "ldapID", "flags": "patch"}),
                     (RefProp("roles", qopt=selectinload),
                      RefProp("properties", flags="patch, managed", link="name", flat="val", qopt=selectinload),
                      RefProp("aliases", flags="patch, managed", link="aliasname", flat="aliasname", qopt=selectinload),
                      BoolP("pop3_imap", flags="patch"),
                      BoolP("smtp", flags="patch"),
                      BoolP("changePassword", flags="patch"),
                      BoolP("publicAddress", flags="patch")),
                     ({"attr": "password", "flags": "init, hidden"},))

    POP3_IMAP = 1 << 0
    SMTP = 1 << 1
    CHGPASSWD = 1 << 2
    PUBADDR = 1 << 3

    MAILUSER = 0x0
    DISTLIST = 0x1
    FORUM = 0x2
    AGENT = 0x3
    ORGANIZATION = 0x4
    PRIVATE_DISTLIST = 0x5
    REMOTE_MAILUSER = 0x6
    ROOM = 0x7
    EQUIPMENT = 0x8
    SEC_DISTLIST = 0x9
    CONTAINER = 0x100
    TEMPLATE = 0x101
    ADDRESS_TEMPLATE = 0x102
    SEARCH = 0x200

    @staticmethod
    def checkCreateParams(data):
        from orm.domains import Domains
        from tools.license import getLicense
        if Users.count() >= getLicense().users:
            return "License user limit exceeded"
        if "domainID" in data:
            domain = Domains.query.filter(Domains.ID == data.get("domainID")).first()
        elif "@" in data["username"]:
            domain = Domains.query.filter(Domains.domainname == data["username"].split("@")[1]).first()
        else:
            domain = None
        if domain is None:
            return "Invalid domain"
        if "@" in data["username"] and domain.domainname != data["username"].split("@", 1)[1]:
            return "Domain specifications do not match"
        data["domain"] = domain
        data["domainID"] = domain.ID
        domainUsers = Users.count(Users.domainID == domain.ID)
        if domain.maxUser <= domainUsers:
            return "Maximum number of domain users reached"
        if data.get("groupID"):
            group = Groups.query.filter(Groups.ID == data.get("groupID"), Groups.domainID == domain.ID).first()
            if group is None:
                return "Invalid group"
        else:
            data["groupID"] = 0
        data["domainStatus"] = domain.domainStatus
        if "properties" not in data:
            data["properties"] = {}
        properties = data["properties"]
        if "storagequotalimit" not in properties:
            data["properties"]["storagequotalimit"] = 0
        for prop in ("prohibitreceivequota", "prohibitsendquota"):
            if prop not in properties:
                properties[prop] = properties["storagequotalimit"]
        properties["creationtime"] = datetime.now()
        if "displaytypeex" not in properties:
            properties["displaytypeex"] = 0

    def __init__(self, props, *args, **kwargs):
        self._permissions = None
        if props is None:
            return
        status = props.pop("domainStatus") << 4
        self.fromdict(props, *args, **kwargs)
        self.addressStatus = (self.addressStatus or 0) | status

    def fromdict(self, patches, *args, **kwargs):
        if "username" in patches:
            from orm.domains import Domains
            username = patches.pop("username")
            domain = patches.pop("domain", None) or Domains.query.filter(Domains.ID == self.domainID).first()
            if "@" in username:
                if username.split("@",1)[1] != domain.domainname:
                    raise ValueError("Domain specifications mismatch.")
                self.username = username
            else:
                self.username = username+"@"+domain.domainname
        DataModel.fromdict(self, patches, args, kwargs)
        displaytype = self.propmap.get("displaytypeex", 0)
        if displaytype in (0, 1, 7, 8):
            self._deprecated_addressType, self._deprecated_subType = self._decodeDisplayType(displaytype)

    @staticmethod
    def _decodeDisplayType(displaytype):
        if displaytype == 0:
            return 0, 0
        elif displaytype == 1:
            return 2, 0
        elif displaytype == 7:
            return 0, 1
        elif displaytype == 8:
            return 0, 2
        raise ValueError("Unknown display type "+str(displaytype))


    def baseName(self):
        return self.username.rsplit("@", 1)[0]

    def domainName(self):
        return self.username.rsplit("@", 1)[0] if "@" in self.username else None

    def permissions(self):
        if self.ID == 0:
            from tools.permissions import Permissions
            return Permissions.sysadmin()
        if not hasattr(self, "_permissions") or self._permissions is None:
            from .roles import AdminUserRoleRelation as AURR, AdminRolePermissionRelation as ARPR, AdminRoles as AR
            from tools.permissions import Permissions
            perms = ARPR.query.filter(AURR.userID == self.ID).join(AR).join(AURR).all()
            self._permissions = Permissions.fromDB(perms)
        return self._permissions

    def getProp(self, name):
        return self.properties[name].val if name in self.properties else None

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, pw):
        self._password = crypt.crypt(pw, crypt.mksalt(crypt.METHOD_MD5))

    def chkPw(self, pw):
        return crypt.crypt(pw, self.password) == self.password

    @property
    def propmap(self):
        return {k: v.val for k, v in self.properties.items()}

    @property
    def propmap_id(self):
        return {p.tag: p.val for p in self.properties.values()}

    def _setPB(self, bit, val):
        self.privilegeBits = (self.privilegeBits or 0) | bit if val else (self.privilegeBits or 0) & ~bit

    def _getPB(self, bit):
        return bool((self.privilegeBits or 0) & bit) if isinstance(self, Users) else self.privilegeBits

    @hybrid_property
    def pop3_imap(self):
        return self._getPB(self.POP3_IMAP)

    @pop3_imap.setter
    def pop3_imap(self, val):
        self._setPB(self.POP3_IMAP, val)

    @pop3_imap.expression
    def pop3_imap(cls):
        return cls.privilegeBits.op("&")(cls.POP3_IMAP)

    @hybrid_property
    def smtp(self):
        return self._getPB(self.SMTP)

    @smtp.setter
    def smtp(self, val):
        self._setPB(self.SMTP, val)

    @smtp.expression
    def smtp(cls):
        return cls.privilegeBits.op("&")(cls.SMTP)

    @hybrid_property
    def changePassword(self):
        return self._getPB(self.CHGPASSWD)

    @changePassword.setter
    def changePassword(self, val):
        self._setPB(self.CHGPASSWD, val)

    @changePassword.expression
    def changePassword(cls):
        return cls.privilegeBits.op("&")(cls.CHGPASSWD)

    @hybrid_property
    def publicAddress(self):
        return self._getPB(self.PUBADDR)

    @publicAddress.setter
    def publicAddress(self, val):
        self._setPB(self.PUBADDR, val)

    @publicAddress.expression
    def publicAddress(cls):
        return cls.privilegeBits.op("&")(cls.PUBADDR)

    @property
    def ldapID(self):
        from tools.ldap import escape_filter_chars
        return None if self.externID is None else escape_filter_chars(self.externID)

    @ldapID.setter
    def ldapID(self, value):
        from tools.ldap import unescapeFilterChars
        self.externID = None if value is None else unescapeFilterChars(value)

    @staticmethod
    def count(*filters):
        """Count users.

        Applies filters to only count real users (DISPLAYTYPEEX == 0) and ignore the admin user (ID == 0).

        Parameters
        ----------
        filters : iterable, optional
            Additional filter expressions to use. The default is ().

        Returns
        -------
        int
            Number of users
        """
        return Users.query.with_entities(Users.ID)\
                          .join(UserProperties, (UserProperties.userID == Users.ID) & (UserProperties.tag == 0x39050003))\
                          .filter(Users.ID != 0, UserProperties._propvalstr == "0", *filters)\
                          .count()

    def delete(self):
        """Delete user from database.

        Also cleans up entries in forwards, members and associations tables.

        Returns
        -------
        str
            Error message or None if successful.
        """
        from .mlists import Associations
        from .misc import Forwards
        from .classes import Members
        if self.ID == 0:
            return "Cannot delete superuser"
        Forwards.query.filter(Forwards.username == self.username).delete(synchronize_session=False)
        Members.query.filter(Members.username == self.username).delete(synchronize_session=False)
        Associations.query.filter(Associations.username == self.username).delete(synchronize_session=False)
        DB.session.delete(self)


class UserProperties(DataModel, DB.Model):
    __tablename__ = "user_properties"

    supportedTypes = PropTypes.intTypes | PropTypes.floatTypes | {PropTypes.STRING, PropTypes.WSTRING}

    userID = DB.Column("user_id", INTEGER(unsigned=True), ForeignKey(Users.ID), primary_key=True)
    tag = DB.Column("proptag", INTEGER(unsigned=True), primary_key=True, index=True)
    _propvalbin = DB.Column("propval_bin", DB.VARBINARY(4096))
    _propvalstr = DB.Column("propval_str", DB.VARCHAR(4096))

    user = relationship(Users)

    _dictmapping_ = (({"attr": "name", "flags": "init"}, {"attr": "val", "flags": "patch"}), (Int("userID"),))

    def __init__(self, props, user, *args, **kwargs):
        self.user = user
        if "tag" in props and props["tag"] & 0xFFFF not in self.supportedTypes:
            raise NotImplementedError("Prop type is currently not supported")
        self.fromdict(props, *args, **kwargs)

    @property
    def name(self):
        if self.tag is None:
            return None
        tagname = PropTags.lookup(self.tag, None)
        return tagname.lower() if tagname else "<unknown>"

    @name.setter
    def name(self, value):
        tag = getattr(PropTags, value.upper(), None)
        if tag is None:
            raise ValueError("Unknown PropTag '{}'".format(value))
        if tag & 0xFFFF not in self.supportedTypes:
            raise ValueError("{}: Tag type {} is not supported".format(PropTags.lookup(tag), PropTypes.lookup(tag)))
        self.tag = tag

    @property
    def type(self):
        return self.tag & 0xFFFF

    @property
    def val(self):
        if self.type == PropTypes.BINARY:
            return self._propvalbin
        if self.type == PropTypes.FILETIME:
            return datetime.fromtimestamp(nxTime(int(self._propvalstr))).strftime("%Y-%m-%d %H:%M:%S")
        return PropTypes.pyType(self.type)(self._propvalstr)

    @val.setter
    def val(self, value):
        if self.type == PropTypes.FILETIME:
            if not isinstance(value, datetime):
                try:
                    value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                except TypeError:
                    raise ValueError("Invalid date '{}'".format(value))
            value = ntTime(time.mktime(value.timetuple()))
        if type(value) != PropTypes.pyType(self.type):
            raise ValueError("Type of value {} does not match type of tag {} ({})".format(value, self.name,
                                                                                          PropTypes.lookup(self.tag)))
        if self.type == PropTypes.BINARY:
            self._propvalbin = value
        else:
            self._propvalstr = str(value)


class Aliases(DataModel, DB.Model):
    __tablename__ = "aliases"

    emailRe = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")

    aliasname = DB.Column("aliasname", DB.VARCHAR(128), nullable=False, unique=True, primary_key=True)
    mainname = DB.Column("mainname", DB.VARCHAR(128), ForeignKey(Users.username, ondelete="cascade", onupdate="cascade"),
                         nullable=False, index=True)

    main = relationship(Users)

    _dictmapping_ = ((Text("aliasname", flags="init"),),
                     (Text("mainname", flags="init"),))

    def __init__(self, aliasname, main, *args, **kwargs):
        if main.ID == 0:
            raise ValueError("Cannot alias superuser")
        self.main = main
        self.fromdict(aliasname)

    def fromdict(self, aliasname, *args, **kwargs):
        if not self.emailRe.match(aliasname):
            raise ValueError("'{}' is not a valid email address".format(aliasname))
        self.aliasname = aliasname
        return self



from . import roles
