# -*- coding: utf-8 -*-
"""
Created on Tue Jun 23 13:59:32 2020

@author: Julia Schroeder, julia.schroeder@grammm.com
@copyright: Grammm GmbH, 2020
"""

from . import DB
from .DataModel import DataModel, Id, Text, Int, Date, BoolP

from sqlalchemy.dialects.mysql import INTEGER, TINYINT

import crypt


class Groups(DataModel, DB.Model):
    __tablename__ = "groups"

    ID = DB.Column("id", INTEGER(10, unsigned=True), nullable=False, primary_key=True, unique=True)
    groupname = DB.Column("groupname", DB.VARCHAR(128), nullable=False, unique=True)
    password = DB.Column("password", DB.VARCHAR(40), nullable=False, server_default="")
    domainID = DB.Column("domain_id", INTEGER(10, unsigned=True), nullable=False, index=True)
    maxSize = DB.Column("max_size", INTEGER(10, unsigned=True), nullable=False)
    maxUser = DB.Column("max_user", INTEGER(10, unsigned=True), nullable=False)
    title = DB.Column("title", DB.VARCHAR(128), nullable=False)
    createDay = DB.Column("create_day", DB.DATE, nullable=False)
    privilegeBits = DB.Column("privilege_bits", INTEGER(10, unsigned=True), nullable=False)
    groupStatus = DB.Column("group_status", TINYINT, nullable=False, server_default="0")

    _dictmapping_ = ((Id(), Text("groupname", flags="patch")),
                     (Text("password", flags="patch"),
                      Id("domainID", flags="patch"),
                      Int("maxSize", flags="patch"),
                      Int("maxUser", flags="patch"),
                      Text("title", flags="patch"),
                      Date("createDay", flags="patch"),
                      Int("privilegeBits", flags="patch"),
                      Int("groupStatus", flags="patch"),
                      BoolP("backup", flags="patch"),
                      BoolP("monitor", flags="patch"),
                      BoolP("log", flags="patch"),
                      BoolP("account", flags="patch")))

    BACKUP = 1 << 0
    MONITOR = 1 << 1
    LOG = 1 << 2
    ACCOUNT = 1 << 3
    DOMAIN_BACKUP = 1 << 8
    DOMAIN_MONITOR = 1 << 9

    def _setFlag(self, flag, val):
        self.privilegeBits = (self.privilegeBits or 0) | flag if val else (self.privilegeBits or 0) & ~flag

    def _getFlag(self, flag):
        return bool(self.privilegeBits or 0 & flag)

    @property
    def backup(self):
        return self._getFlag(self.BACKUP)

    @backup.setter
    def backup(self, val):
        self._setFlag(self.BACKUP, val)

    @property
    def monitor(self):
        return self._getFlag(self.MONITOR)

    @monitor.setter
    def monitor(self, val):
        self._setFlag(self.MONITOR, val)

    @property
    def log(self):
        return self._getFlag(self.LOG)

    @log.setter
    def log(self, val):
        self._setFlag(self.LOG, val)

    @property
    def account(self):
        return self._getFlag(self.ACCOUNT)

    @account.setter
    def account(self, val):
        self._setFlag(self.ACCOUNT, val)

    @property
    def domainBackup(self):
        return self._getFlag(self.DOMAIN_BACKUP)

    @domainBackup.setter
    def domainBackup(self, val):
        self._setFlag(self.DOMAIN_BACKUP, val)

    @property
    def domainMonitor(self):
        return self._getFlag(self.DOMAIN_MONITOR)

    @domainMonitor.setter
    def domainMonitor(self, val):
        self._setFlag(self.DOMAIN_MONITOR, val)


class Users(DataModel, DB.Model):
    __tablename__ = "users"

    ID = DB.Column("id", INTEGER(10, unsigned=True), nullable=False, primary_key=True, unique=True)
    username = DB.Column("username", DB.VARCHAR(128), nullable=False, unique=True)
    _password = DB.Column("password", DB.VARCHAR(40), nullable=False, server_default="")
    realName = DB.Column("real_name", DB.VARCHAR(32), nullable=False, server_default="")
    title = DB.Column("title", DB.VARCHAR(128), nullable=False, server_default="")
    memo = DB.Column("memo", DB.VARCHAR(128), nullable=False, server_default="")
    domainID = DB.Column("domain_id", INTEGER(10, unsigned=True), nullable=False, index=True)
    groupID = DB.Column("group_id", INTEGER(10, unsigned=True), nullable=False, index=True)
    maildir = DB.Column("maildir", DB.VARCHAR(128), nullable=False, server_default="")
    maxSize = DB.Column("max_size", INTEGER(10, unsigned=True), nullable=False)
    maxFile = DB.Column("max_file", INTEGER(10, unsigned=True), nullable=False)
    createDay = DB.Column("create_day", DB.DATE, nullable=False)
    lang = DB.Column("lang", DB.VARCHAR(32), nullable=False, server_default="")
    timezone = DB.Column("timezone", DB.VARCHAR(64), nullable=False, server_default="")
    mobilePhone = DB.Column("mobile_phone", DB.VARCHAR(20), nullable=False, server_default="")
    privilegeBits = DB.Column("privilege_bits", INTEGER(10, unsigned=True), nullable=False)
    subType = DB.Column("sub_type", TINYINT, nullable=False, server_default='0')
    addressStatus = DB.Column("address_status", TINYINT, nullable=False, server_default="0")
    addressType = DB.Column("address_type", TINYINT, nullable=False, server_default="0")
    cell = DB.Column("cell", DB.VARCHAR(20), nullable=False, server_default="")
    tel = DB.Column("tel", DB.VARCHAR(20), nullable=False, server_default="")
    nickname = DB.Column("nickname", DB.VARCHAR(32), nullable=False, server_default="")
    homeaddress = DB.Column("homeaddress", DB.VARCHAR(128), nullable=False, server_default="")

    _dictmapping_ = ((Id(), Text("username", flags="patch")),
                     (Text("realName", flags="patch"),
                      Text("title", flags="patch"),
                      Text("memo", flags="patch"),
                      Id("domainID", flags="patch"),
                      Id("groupID", flags="patch"),
                      Text("maildir", flags="patch"),
                      Int("maxSize", flags="patch"),
                      Int("maxFile", flags="patch"),
                      Date("createDay", flags="patch"),
                      Text("lang", flags="patch"),
                      Text("timezone", flags="patch"),
                      Text("mobilePhone", flags="patch"),
                      Int("subType", flags="patch"),
                      Int("addressStatus", flags="patch"),
                      Text("cell", flags="patch"),
                      Text("tel", flags="patch"),
                      Text("nickname", flags="patch"),
                      Text("homeaddress", flags="patch"),
                      BoolP("pop3_imap", flags="patch"),
                      BoolP("smtp", flags="patch"),
                      BoolP("changePassword", flags="patch"),
                      BoolP("publicAddress", flags="patch"),
                      BoolP("netDisk", flags="patch")))

    POP3_IMAP = 1 << 0
    SMTP = 1 << 1
    CHGPASSWD = 1 << 2
    PUBADDR = 1 << 3
    NETDISK = 1 << 4

    def _setFlag(self, flag, val):
        self.privilegeBits = (self.privilegeBits or 0) | flag if val else (self.privilegeBits or 0) & ~flag

    def _getFlag(self, flag):
        return bool(self.privilegeBits or 0 & flag)

    @property
    def pop3_imap(self):
        return self._getFlag(self.POP3_IMAP)

    @pop3_imap.setter
    def pop3_imap(self, val):
        self._setFlag(self.POP3_IMAP, val)

    @property
    def smtp(self):
        return self._getFlag(self.SMTP)

    @smtp.setter
    def smtp(self, val):
        self._setFlag(self.SMTP, val)

    @property
    def changePassword(self):
        return self._getFlag(self.CHGPASSWD)

    @changePassword.setter
    def changePassword(self, val):
        self._setFlag(self.CHGPASSWD, val)

    @property
    def publicAddress(self):
        return self._getFlag(self.PUBADDR)

    @publicAddress.setter
    def publicAddress(self, val):
        self._setFlag(self.PUBADDR, val)

    @property
    def netDisk(self):
        return self._getFlag(self.NETDISK)

    @netDisk.setter
    def netDisk(self, val):
        self._setFlag(self.NETDISK, val)

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, pw):
        self._password = crypt.crypt(pw, crypt.mksalt(crypt.METHOD_MD5))

    def chkPw(self, pw):
        return crypt.crypt(pw, self.password) == self.password



DB.Index(Users.domainID, Users.username, unique=True)
DB.Index(Users.groupID, Users.username, unique=True)
DB.Index(Users.maildir, Users.addressType)
