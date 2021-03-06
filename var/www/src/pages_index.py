# Copyright 2008 Lee Harr
#
# This file is part of TZMud.
#
# TZMud is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# TZMud is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with TZMud.  If not, see <http://www.gnu.org/licenses/>.


from operator import attrgetter, itemgetter
from nevow import tags as T

import pages_base
from pages_base import xmlf

import wizard
import admin

class Dummy(object):
    pass

class Index(pages_base.TZPage):
    docFactory = xmlf('index.html')
    title = 'TZMud Web Interace'

    def render_index_players(self, ctx, data):
        data.sort(key=attrgetter('name'))
        lines = []
        for player in data:
            line = []
            name = player.name
            tzid = player.tzid
            tzidcell = T.td(_class="objtzid")[tzid, ':']
            line.append(tzidcell)


            if admin.verify(player):
                line.append(T.td['!'])
            elif wizard.verify(player):
                line.append(T.td['@'])
            else:
                line.append(T.td)

            editlink = T.a(href="/edit/%s" % tzid)[name]
            line.append(T.td(_class="objname")[editlink])

            if player.logged_in:
                room = player.room
                editlink = "/edit/%s" % room.tzid
                link = T.a(href=editlink)[T.span(_class="editlink")[room.name]]
                line.append(T.td[link])
            else:
                line.append(T.td)

            lines.append(T.tr[line])

        return T.table[lines]

    def render_index_rooms(self, ctx, data):
        lines = []
        data.sort(key=attrgetter('name'))
        for room in data:
            editlink = T.a(href="/edit/%s" % room.tzid)[room.name]
            tzid = T.td(_class="roomtzid")[room.tzid, ':']
            #name = T.td(_class="roomname")[room.name]
            name = T.td(_class="roomname")[editlink]
            if not room.exits():
                row = T.tr(_class='warn')
            else:
                row = T.tr
            lines.append(row[tzid, name])

        return T.table[lines]

    def render_idtable(self, ctx, data):
        lines = []
        for obj in data:
            editlink = T.a(href="/edit/%s" % obj.tzid)[obj.name]
            tzid = T.td(_class="objtzid")[obj.tzid, ':']
            #name = T.td(_class="objname")[obj.name]
            name = T.td(_class="objname")[editlink]
            lines.append(T.tr[tzid, name])
        return T.table[lines]

    def render_idtable_sortalpha(self, ctx, data):
        data.sort(key=attrgetter('name'))
        return self.render_idtable(ctx, data)

    def render_idtable_sortid(self, ctx, data):
        data.sort(key=attrgetter('tzid'))
        return self.render_idtable(ctx, data)
