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


'''Basic player commands.

Docstrings for these functions are used to generate the help entries
from inside the MUD.

Each function takes two parameters:
    s -> Connection protocol instance (might read this a "self", and think
            of these functions as methods on the protocol object...)
    r -> result returned by the command parser.

Optional command parameters are shown in the docstring in [square brackets].
A notation like <item> means either the name of the item, or the id number
of the object specified as #nnn (ie #4 or #26).

Options separated by a vertical bar | indicate that one should be chosen.

'''

import copy
import time

import wizard
import admin

import players
import mobs

from share import find

from colors import blue, red, green, yellow, bold

import conf


def cmd_look(s, r):
    '''look  [[at] <item>|<player>|<mob>|<room>|<exit>]

    Examine some object, player, room, etc more closely.

    You can also say:   look [at] self | myself | me   or
        look around | look about | look [at] the room

    Alternate: l

    '''

    player = s.player
    room = s.room
    obj = find(r, room, player, room)

    if obj is None:
        objname = r.get('objname', '')
        if objname.lower() in ('self', 'myself', 'me'):
            obj = player
        elif objname.lower() in ('around', 'about', 'the room'):
            obj = room

    if obj is not None and player.can_see(obj):
        if obj is not player:
            s.message('You look at the', obj, '.')
        else:
            s.message('You look at yourself.')
        msg = player.look_at(obj)
        if msg:
            s.mlmessage(msg)
        else:
            s.message('Nothing special.')
        s.room.action(dict(act='look', actor=player, actee=obj))
    else:
        s.message('You do not see that here.')


def cmd_info(s, r):
    '''info [<item>|<player>|<mob>|<room>|<exit>]

    Get more info about given object or about own player if none given

    '''

    objs = find(r, s.room, s.player, s.player, all=True)
    objs = filter(s.player.can_see, objs)

    if objs:
        for obj in objs:
            s.mlmessage(obj.info())
    else:
        s.message('You do not see that here.')


def cmd_time(s, r=None):
    '''Show the current time according to the game server.'''

    s.message(time.ctime())


def cmd_get(s, r):
    '''get [the] <item>

    Pick up something and put it in your inventory.

    Alternate: take

    '''

    objname = r.get('objname', '')
    objtzid = r.get('objtzid', '')
    if not objname and not objtzid:
        s.message('Try: get <item>')
        raise SyntaxError

    if objname == 'all':
        for item in filter(s.player.can_see, s.room.items()):
            if s.player.get_item(item, s.room):
                s.player.message('You get the', item, '.')
        return

    item = find(r, s.room)
    if not s.player.can_see(item):
        allitems = find(r, s.room, all=True)
        if allitems is not None:
            iis = filter(s.player.can_see, allitems)
            if iis:
                item = iis[0]
            else:
                item = None
        else:
            item = None
    have = s.player.itemname(objname) or s.player.item(objtzid)

    if item:
        if item.gettable:
            if s.player.get_item(item, s.room):
                s.player.message('You get the', item, '.')
        else:
            s.message('You cannot get that.')

    elif have:
        s.message('You already have that.')

    else:
        s.message('You do not see that here.')

def cmd_drop(s, r):
    '''drop <item>

    Drop something from your inventory.

    '''

    objname = r.get('objname', '')
    objtzid = r.get('objtzid', '')
    if not objname and not objtzid:
        s.message('Try: drop <item>')
        raise SyntaxError

    number = r.get('number', '')

    if objname == 'all':
        for item in s.player.items():
            s.player.drop_item(item)
            s.player.message('You drop the', item, '.')
        return

    item = s.player.itemname(objname) or s.player.item(objtzid)

    if item is not None:
        if number:
            if hasattr(item, 'split'):
                try:
                    item = item.split(number)
                except ValueError:
                    s.message('You do not have that many.')
                    return
            elif number == 1:
                pass
            else:
                s.message('You cannot split that item.')

        s.player.drop_item(item)
        s.player.message('You drop the', item, '.')

    else:
        s.message('You do not have that.')

def cmd_put(s, r):
    '''put <item> in <container>

    Put some item inside of a container.

    '''

    objname = r.get('objname', '')
    objtzid = r.get('objtzid', 0)
    if not objname and not objtzid:
        s.message('Try: put <item> in <container>')
        raise SyntaxError

    obj2name = r.get('obj2name', '')
    obj2tzid = r.get('obj2tzid', 0)

    player = s.player
    room = s.room

    container = player.itemname(obj2name) or room.itemname(obj2name) or \
                    player.item(obj2tzid) or room.item(obj2tzid)

    if container is None:
        if obj2name:
            s.message('You do not have a container called', obj2name, '.')
            return
        else:
            s.message('You do not have such a container.')
            return
    elif not hasattr(container, 'add'):
        s.message("You can't put anything in there.")
        return

    item = player.itemname(objname) or room.itemname(objname) or \
                player.item(objtzid) or room.item(objtzid)

    if item is None:
        if objname == 'all':
            for item in filter(s.player.can_see, s.player.items()):
                if item is not container:
                    cmd_put(s, dict(objtzid=item.tzid, obj2tzid=container.tzid))
            return
        else:
            s.message('You do not have that.')
            return

    if player.is_wearing(item):
        player.unwear(item)
        item.unwear(player)
    player.remove(item)
    room.remove(item)

    s.message('You put the', item, 'in the', container, '.')
    item.put(player, container)
    if item.exists():
        container.add(item)
    room.action(dict(act='put', actor=player, item=item, container=container))


def cmd_take(s, r):
    '''take <item> from <container>

    Remove some item from inside of a container.

    Alternate: remove

    '''

    objname = r.get('objname', '')
    objtzid = r.get('objtzid', 0)
    if not objname and not objtzid:
        s.message('Try: take <item> from <container>')
        raise SyntaxError
    number = r.get('number', '')

    obj2name = r.get('obj2name', '')
    obj2tzid = r.get('obj2tzid', 0)

    player = s.player
    room = s.room

    container = player.itemname(obj2name) or room.itemname(obj2name) or \
                    player.item(obj2tzid) or room.item(obj2tzid)

    if container is None:
        if obj2name:
            s.message('You do not have', obj2name, '.')
        else:
            s.message('You do not have object #', obj2tzid, '.')
        return

    if hasattr(container, 'remove'):
        item = container.itemname(objname) or container.item(objtzid)
        if item is not None:
            if number:
                if hasattr(item, 'split'):
                    try:
                        item = item.split(number)
                    except ValueError:
                        s.message('You do not have that many.')
                        return
                elif number == 1:
                    pass
                else:
                    s.message('You cannot split that item.')

            container.remove(item)

            s.message('You take the', item, 'from the', container, '.')
            item.take(player, container)
            if item.exists():
                player.add(item)
            room.action(dict(act='take', actor=player, item=item,
                                container=container))

        else:
            if objname:
                if objname == 'all':
                    for item in filter(s.player.can_see, container.items()):
                        cmd_take(s, dict(objtzid=item.tzid, obj2tzid=container.tzid))
                    return
                else:
                    s.message('There is no', objname, 'in', container.name, '.')
            else:
                s.message('There is no object #', objtzid, 'in', container.name, '.')

    else:
        s.message('That is not a container.')


def cmd_use(s, r):
    '''use <item> [on <object>]

    Use the given item, if that makes sense. Use it on the
        given object, if given.

    '''

    objname = r.get('objname', '')
    objtzid = r.get('objtzid', 0)
    if not objname and not objtzid:
        s.message('Try: use <item>')
        raise SyntaxError

    obj2name = r.get('obj2name', '')
    obj2tzid = r.get('obj2tzid', 0)

    player = s.player

    item = player.itemname(objname) or player.item(objtzid)
    if item is None:
        s.message('You do not have that.')
        return
    else:
        use = getattr(item, 'use', None)
        if use is None:
            s.message('You cannot use that.')
            return
        else:
            findr = dict(objname=obj2name, objtzid=obj2tzid)
            obj = find(findr, s.room, player)
            if (obj2name or obj2tzid) and obj is None:
                s.message("You cannot use it on that. It's not here.")
                return
            else:
                use(player, obj)


def cmd_inventory(s, r=None):
    '''inventory

    Look at what you are holding in your inventory.

    Alternates: inv i

    '''

    if s.player.items():
        s.message('You are holding:')
        for item in s.player.items():
            if s.player.is_wearing(item):
                msg = unicode(item) + '*'
            else:
                msg = unicode(item)
            s.message(msg, indent=4)
    else:
        s.message('You have nothing.')


def cmd_wear(s, r):
    '''wear <item>

    Don some wearable item from your inventory.

    '''

    objname = r.get('objname', '')
    objtzid = r.get('objtzid', 0)
    if not objname and not objtzid:
        s.message('Try: wear <item>')
        raise SyntaxError

    player = s.player

    if objname:
        iis = player.itemname(objname, all=True)
        item = None
        if iis is not None:
            for i in iis:
                item = i
                if not player.is_wearing(i):
                    break

    else:
        item = player.item(objtzid)

    if item is None:
        s.message('You do not have that.')
    elif player.is_wearing(item):
        s.message('You are already wearing that.')
    elif not item.wearable:
        s.message("You can't wear that.")
    else:
        if player.wear(item):
            s.message('You wear the', item, '.')
        else:
            s.message('You try to wear the', item, "but can't.")


def cmd_remove(s, r):
    '''remove <item> OR remove <item> from <container>

    Remove some wearable item that you are wearing or,
        remove some item from a container.

    '''

    # Note that the code for removing an item from a container is
    #   actually in cmd_take, not here.

    objname = r.get('objname', '')
    objtzid = r.get('objtzid', 0)
    if not objname and not objtzid:
        s.message('Try: remove <item>')
        raise SyntaxError

    player = s.player

    if objname:
        iis = player.itemname(objname, all=True)
        item = None
        if iis is not None:
            for i in iis:
                item = i
                if player.is_wearing(i):
                    break

    else:
        item = player.item(objtzid)

    if item is None or not player.is_wearing(item):
        s.message('You are not wearing that.')
    else:
        if player.unwear(item):
            s.message('You remove the', item, '.')
        else:
            s.message('You try to remove the', item, "but can't.")


def cmd_go(s, r):
    '''go [to] [<exit>|<room>]

    Go through the given exit or to the given room. No need to specify
        the name of the exit or room if there is only one way out.

    Alternates: enter [<exit>] or <exit> or [out|exit|leave]

    Examples:
        house
        > exits
        Exits:
            east, north
        > east
        place
        > exits
        Exits:
            west
        > leave
        house
        > enter place
        place
        > exit
        house
        > east
        place

    '''

    # return True if the player has successfully taken the exit to
    #   its destination.
    # return False if that is a possible exit, but something prevented
    #   the player from taking the exit, ie it is locked or it weighs
    #   too much to push it open.
    # return None if there is no such exit or room that can be taken
    #   from this location.

    objname = r.get('objname', '')
    objtzid = r.get('objtzid', '')
    implied = r.get('implied', False) # set True in tzprotocol.py::dispatch
                                        # when text is not found to be a
                                        # command and we are looking to
                                        # see if the word is the name of a
                                        # place the player is trying to go to
                                        # or the name of an exit to take

    origin = s.room
    x = origin.exitname(objname) or origin.exit(objtzid)
    if x is None:
        xs = origin.exits()
        xs = filter(s.player.can_see, xs)

        found = False
        if objname:
            for x in xs:
                if found:
                    break

                dest = x.destination

                if dest is not None:
                    if dest.name == objname:
                        found = True
                        break

                    if hasattr(dest, 'name_aka'):
                        for aka in dest.name_aka:
                            if aka == objname:
                                found = True
                                break

        alternates = ['out', 'exit', 'leave']

        if found:
            pass
        elif (objname.lower() in alternates) or (not objname and not objtzid):
            if len(xs)==1:
                x = xs[0]
            else:
                if not objname:
                    objname = 'go'
                s.message(objname, 'through which exit?')
                return None
        else:
            if not implied:
                s.message("You can't go that way.")
            return None

    success, msg = s.player.go(x)

    if success:
        s.message(x.destination)

        ps = filter(s.player.can_see, s.room.players())
        for player in ps:
            if player != s.player:
                s.message(player, 'is here.')
                if player.following == player:
                    s.message('You are following', player, '.')

        ms = filter(s.player.can_see, s.room.mobs())
        for mob in ms:
            s.message(mob, 'is here.')
            if player.following == mob:
                s.message('You are following', mob, '.')

    else:
        s.message(msg)

    return success

def cmd_lock(s, r):
    '''lock <door> [with <key>]

    Lock the door, if you have the correct key.

    If <key> is not specified, will try all of the keys to
        see if one will lock the door.

    '''

    objname = r.get('objname', '')
    objtzid = r.get('objtzid', 0)
    if not objname and not objtzid:
        s.message('Lock which door?')
        return

    x = s.room.exitname(objname) or s.room.exit(objtzid)
    if x is None:
        s.message('No such exit.')
        return

    keyname = r.get('obj2name', '')
    keytzid = r.get('obj2tzid', 0)

    if keyname or keytzid:
        key = s.player.itemname(keyname) or s.player.item(keytzid)
    else:
        key = None
        nkeys = 0
        for item in s.player.items():
            if hasattr(item, 'name_aka'):
                for name in item.name_aka:
                    if name == 'key':
                        nkeys += 1
                        if item.locks(x):
                            key = item

    if key is None:
        if not keyname and not keytzid:
            if nkeys > 0:
                s.message('None of your keys fit.')
            else:
                s.message('Lock it with what?')
        else:
            s.message('You do not have such a key.')
        return

    if key.locks(x):
        x.lock(key)
        s.message('You lock the door', x, 'with key', key, '.')
        s.room.action(dict(act='lock', actor=s.player, door=x, key=key))
    else:
        s.message('That key does not fit.')
        s.room.action(dict(act='lockfail', actor=s.player, door=x, key=key))


def cmd_unlock(s, r):
    '''unlock <door> [with <key>]

    Unlock the door, if you have the correct key.

    If <key> is not specified, will try all of the keys to
        see if one will unlock the door.

    '''

    objname = r.get('objname', '')
    objtzid = r.get('objtzid', 0)
    if not objname and not objtzid:
        s.message('Unlock which door?')
        return

    x = s.room.exitname(objname) or s.room.exit(objtzid)
    if x is None:
        s.message('No such exit.')
        return

    keyname = r.get('obj2name', '')
    keytzid = r.get('obj2tzid', 0)

    if keyname or keytzid:
        key = s.player.itemname(keyname) or s.player.item(keytzid)
    else:
        key = None
        nkeys = 0
        for item in s.player.items():
            if hasattr(item, 'name_aka'):
                for name in item.name_aka:
                    if name == 'key':
                        nkeys += 1
                        if item.locks(x):
                            key = item

    if key is None:
        if not keyname and not keytzid:
            if nkeys > 0:
                s.message('None of your keys fit.')
            else:
                s.message('Unlock it with what?')
        else:
            s.message('You do not have such a key.')
        return

    if key.locks(x):
        x.unlock(key)
        s.message('You unlock the door', x, 'with key', key, '.')
        s.room.action(dict(act='unlock', actor=s.player, door=x, key=key))
    else:
        s.message('That key does not fit.')
        s.room.action(dict(act='lockfail', actor=s.player, door=x, key=key))


def cmd_follow(s, r=None):
    '''follow [<player>|<mob>]

    Follow the give character, or find out who you are following, if no one
        is specified to follow.

    To stop following, "follow none", "follow no one", or "follow nobody".

    '''

    player = s.player
    room = s.room

    objname = r.get('objname', '')
    objtzid = r.get('objtzid', '')

    if not objname and not objtzid:
        if player.following is not None:
            s.message('You are following', player.following, '.')
        else:
            s.message('Not following anyone.')

        return


    character = room.playername(objname) or room.player(objtzid) or \
                room.mobname(objname) or room.mob(objtzid)

    if character is None and objname:
        stoppers = ['none', 'nobody', 'no one']
        if objname.lower() in stoppers:
            player.following = None
            s.message('You stop following.')
            return

    if character is None or not player.can_see(character):
        if objname:
            s.message(objname, 'is not here.')
        elif objtzid:
            s.message('Object #', objtzid, 'is not here.')

    else:
        player.following = character
        if character == player:
            s.message('You stop following.')
        else:
            s.message('You start following', character, '.')
            room.action(dict(act='follow', actor=player, following=character))


def cmd_exits(s, r=None):
    '''exits

    List the room's visible exits.

    '''

    if s.room.exitnames():
        s.message('Exits:')
        xs = s.room.exits()
        xs = filter(s.player.can_see, xs)
        exits = ', '.join(unicode(x) for x in xs)
        s.message(exits, indent=4)
    else:
        s.message('You see no obvious exits.')


def cmd_say(s, r):
    '''say <text>

    Say something to everyone in the same room.

    Alternate: "<text>

    '''

    words = r['message']

    if words.endswith('?'):
        verb = 'ask'
    elif words.endswith('!'):
        verb = 'exclaim'
    else:
        verb = 'say'
    quoted = '"' + words + '"'
    s.message('You', verb+',', quoted)
    s.room.action(dict(act='say', actor=s.player, verb=verb, raw=words))


if conf.talkmode:
    import share
    cmd_tell = share.cmd_tell


def cmd_listen(s, r):
    '''listen [to] <object>

    Put your ear up to some object to see if you can hear something.

    '''

    objname = r.get('objname', '')
    objtzid = r.get('objtzid', '')
    if not objname and not objtzid:
        s.message('Try: listen to <object>')
        raise SyntaxError

    player = s.player
    room = s.room

    obj = player.itemname(objname) or player.item(objtzid) or \
            room.itemname(objname) or room.item(objtzid) or \
            room.exitname(objname) or room.exit(objname)

    if obj is not None:
        s.message('You listen to', obj)
        s.room.action(dict(act='listen', actor=player, obj=obj))
    else:
        s.message('That is not here.')


def cmd_shout(s, r):
    '''shout <text>

    Shout something to everyone in the same room and to
        some surrounding rooms.

    '''

    words = r['message']

    quoted = '"' + words + '"'
    s.message('You shout,', quoted)
    spread = 2
    s.room.action(dict(act='shout', actor=s.player, raw=words, spread=spread))


def cmd_emote(s, r):
    '''emote <text>

    Show some kind of emotion or pose.

    ex: "emote dances around happily" would display "lee dances around happily"
    or  ":laughs" would display "lee laughs"

    Alternate: :<text>

    '''

    words = r['message']

    msg = u'(%s %s)' % (s.player, words)
    s.message(msg)
    s.room.action(dict(act='emote', actor=s.player, raw=words))


def cmd_think(s, r):
    '''think <text>

    Show the text between thought bubbles, to the room where you're on. 
	For example: Andy thinks . o O ( therefore I am )

    '''

    words = r['message']

    msg = u'%s thinks . o O ( %s )' % (s.player, words)
    s.message(msg)
    s.room.action(dict(act='emote', actor=s.player, raw=words))


def cmd_quit(s, r=None):
    '''quit

    Disconnect from the mud.

    '''

    s.transport.loseConnection()


def cmd_who(s, r=None):
    '''who

    List players connected now.

    '''

    s.message('Players connected:')
    for player in s.who():
        s.message(player, indent=4)


def cmd_cls(s, r=None):
    '''cls

    Clears your screen.

    '''
    for lines in range(60): # TODO: of course, we could make the number of lines a configurable number...
        s.message()

def cmd_recap(s, r):
    '''recap <recapped-name>

    Define your character's "recapped name". For instance, if your 
    name is "Montainrat", you can define it to be seen as 
    "MontainRat". You cannot, however, use this command to change 
    your name.
    '''
    recapped = r['message']
    if s.player.name.lower() == recapped.lower():
        s.player.extra_settings['recap'] = blue(recapped)
        s.message('Your name will now be seen by everyone as ' + s.player.extra_settings['recap'])
    else:
        s.message('The recapped name still has to match your proper name.')
 
def cmd_set(s, r=None):
    '''set <var> [= <value>]

    Set the given variable to the specified value, or True.

    Variables available for setting:
        ansi        -- send ANSI color codes
        speech      -- turn on/off speech mode

    '''

    var = r.get('var', None)
    val = r.get('val', True)

    if var is not None:
        try:
            lowerval = val.lower()
        except AttributeError:
            lowerval = None

        if lowerval == 'true':
            val = True
        elif lowerval == 'false':
            val = False

        if val or lowerval=='false':
            # if lowerval is 'false' user specified 'false'
            # if using unset then val will actually be False
            s.player.user_settings[var] = val
        elif var in s.player.user_settings:
            del s.player.user_settings[var]
        else:
            s.player.user_settings[var] = val

    else:
        if s.player.user_settings:
            s.message('Settings:')
            for k, v in s.player.user_settings.items():
                s.message(u'%s = %s' % (k, v), indent=4)
        else:
            s.message('You have not set anything yet.')


def cmd_unset(s, r):
    '''unset <var>

    Equivalent to using: set <var>=False

    If the setting has previously been set (even if set to False),
        removes the setting. Otherwise, sets the given variable to False.

    '''

    var = r.get('var')
    r['verb'] = 'set'
    r['var'] = var
    r['val'] = False
    cmd_set(s, r)


def cmd_stats(s, r=None):
    '''stats

    Show the values of all character statistics.

    '''

    s.message('Character stats...')
    keys = s.player._stats0.keys()
    keys.sort()
    maxlen = max(len(k) for k in keys)
    for k in keys:
        v = s.player.setting(k)
        spaces = maxlen - len(k)
        s.message('    ', k, ' '*spaces, ':', '%4d'%v)


def cmd_password(s, r):
    '''password <old password> <new password>

    Change from old password to new password.

    '''

    oldpwtext = r['old']
    newpwtext = r['new']

    if s.player.check_password(oldpwtext):
    #if True:
        s.player.set_password(newpwtext)
        s.message('Password changed.')
    else:
        s.message('Incorrect password.')


def cmd_xyzzy(s, r=None):
    'xyzzy'

    pass


def cmd_help(s, r=None):
    '''help [<subject>]

    Get help on some <subject> or general help if no subject given.

    '''

    topic = r.get('topic', None)

    import actions
    if topic is None:
        s.message('Available commands:')
        commands = []
        for func in dir(actions):
            if func.startswith('cmd_'):
                #s.message(func[4:], indent=4)
                commands.append(func[4:])
        commands.sort()
        s.columns_v(commands)

        if wizard.verify(s.player):
            s.message('')
            s.message('Use @help for wizard commands')
        if admin.verify(s.player):
            s.message('')
            s.message('Use !help for admin commands')

    else:
        func_name = 'cmd_%s' % topic
        func = getattr(actions, func_name, None)
        if func is not None:
            doc = func.__doc__
            if doc is not None:
                msg = 'Help on %s:' % topic
                s.message(msg)
                s.message()
                msg = doc.split('\n')
                msg.insert(0, 'Syntax:')
                msg[1] = '        ' + msg[1]
                s.mlmessage(msg)
                return

        msg = 'Sorry. No help available on that subject.'
        s.message(msg)

def cmd_map(s, r=None):
    '''map

    Shows you the map.

    '''

    lines = open('MAP').readlines()
    for line in lines:
        s.message(line.rstrip())
