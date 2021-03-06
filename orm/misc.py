# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2020 grammm GmbH

from . import DB

from tools.DataModel import DataModel, Id, Text

from sqlalchemy.dialects.mysql import INTEGER, TINYINT


class Forwards(DataModel, DB.Model):
    __tablename__ = "forwards"

    ID = DB.Column("id", INTEGER(10, unsigned=True), nullable=False, primary_key=True)
    username = DB.Column("username", DB.VARCHAR(128), nullable=False, unique=True)
    forwardType = DB.Column("forward_type", TINYINT, nullable=False)
    destination = DB.Column("destination", DB.VARCHAR(128), nullable=False)

    _dictmapping_ = ((Id(), Text("username", flags="patch")),
                     (Text("forwardType", flags="patch"),
                      Text("destination", flags="patch")))
