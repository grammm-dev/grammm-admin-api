# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2020 grammm GmbH

from . import DB
from tools.DataModel import DataModel, Id, Text, Int, Date, BoolP

from sqlalchemy.dialects.mysql import INTEGER, TINYINT

import crypt
from datetime import datetime


class Orgs(DataModel, DB.Model):
    __tablename__ = "orgs"

    ID = DB.Column("id", INTEGER(10, unsigned=True), unique=True, primary_key=True, nullable=False)
    memo = DB.Column("memo", DB.VARCHAR(128), nullable=False, server_default="")

    _dictmapping_ = ((Id(), Text("memo", flags="patch")),)


class Domains(DataModel, DB.Model):
    __tablename__ = "domains"

    ID = DB.Column("id", INTEGER(10, unsigned=True), unique=True, primary_key=True, nullable=False)
    orgID = DB.Column("org_id", INTEGER(10, unsigned=True), nullable=False, server_default="0", index=True)
    domainname = DB.Column("domainname", DB.VARCHAR(64), nullable=False)
    homedir = DB.Column("homedir", DB.VARCHAR(128), nullable=False, server_default="")
    maxUser = DB.Column("max_user", INTEGER(10, unsigned=True), nullable=False)
    title = DB.Column("title", DB.VARCHAR(128), nullable=False, server_default="")
    address = DB.Column("address", DB.VARCHAR(128), nullable=False, server_default="")
    adminName = DB.Column("admin_name", DB.VARCHAR(32), nullable=False, server_default="")
    tel = DB.Column("tel", DB.VARCHAR(64), nullable=False, server_default="")
    endDay = DB.Column("end_day", DB.DATE, nullable=False, default="3333-03-03")
    domainStatus = DB.Column("domain_status", TINYINT, nullable=False, server_default="0")

    _dictmapping_ = ((Id(), Text("domainname", flags="init")),
                     (Id("orgID", flags="patch"),
                      Int("maxUser", flags="patch"),
                      Text("title", flags="patch"),
                      Text("address", flags="patch"),
                      Text("adminName", flags="patch"),
                      Text("tel", flags="patch"),
                      Date("endDay", flags="patch"),
                      Int("domainStatus", flags="patch")))

    NORMAL = 0
    SUSPENDED = 1
    OUTOFDATE = 2
    DELETED = 3

    def __init__(self, props: dict, *args, **kwargs):
        if "password" in props:
            self.password = props.pop("password")
        DataModel.__init__(self, props, args, kwargs)

    @staticmethod
    def checkCreateParams(data):
        if "maxUser" not in data:
            return "Missing required property maxUser"
