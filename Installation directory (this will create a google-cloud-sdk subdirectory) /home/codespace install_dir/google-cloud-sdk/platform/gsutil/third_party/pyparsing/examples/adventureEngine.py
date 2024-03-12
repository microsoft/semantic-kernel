# adventureEngine.py
# Copyright 2005-2006, Paul McGuire
#
# Updated 2012 - latest pyparsing API
#

from pyparsing import *
import random
import string

def aOrAn( item ):
    if item.desc[0] in "aeiou":
        return "an " + item.desc
    else:
        return "a " + item.desc

def enumerateItems(l):
    if len(l) == 0: return "nothing"
    out = []
    if len(l) > 1:
        out.append(', '.join(aOrAn(item) for item in l[:-1]))
        out.append('and')
    out.append(aOrAn(l[-1]))
    return " ".join(out)

def enumerateDoors(l):
    if len(l) == 0: return ""
    out = []
    if len(l) > 1:
        out.append(', '.join(l[:-1]))
        out.append("and")
    out.append(l[-1])
    return " ".join(out)

class Room(object):
    def __init__(self, desc):
        self.desc = desc
        self.inv = []
        self.gameOver = False
        self.doors = [None,None,None,None]

    def __getattr__(self,attr):
        return \
            {
            "n":self.doors[0],
            "s":self.doors[1],
            "e":self.doors[2],
            "w":self.doors[3],
            }[attr]

    def enter(self,player):
        if self.gameOver:
            player.gameOver = True

    def addItem(self, it):
        self.inv.append(it)

    def removeItem(self,it):
        self.inv.remove(it)

    def describe(self):
        print(self.desc)
        visibleItems = [ it for it in self.inv if it.isVisible ]
        if random.random() > 0.5:
            if len(visibleItems) > 1:
                is_form = "are"
            else:
                is_form = "is"
            print("There {0} {1} here.".format(is_form, enumerateItems(visibleItems)))
        else:
            print("You see %s." % (enumerateItems(visibleItems)))


class Exit(Room):
    def __init__(self):
        super(Exit,self).__init__("")

    def enter(self,player):
        player.gameOver = True



class Item(object):
    items = {}
    def __init__(self, desc):
        self.desc = desc
        self.isDeadly = False
        self.isFragile = False
        self.isBroken = False
        self.isTakeable = True
        self.isVisible = True
        self.isOpenable = False
        self.useAction = None
        self.usableConditionTest = None
        self.cantTakeMessage = "You can't take that!"
        Item.items[desc] = self

    def __str__(self):
        return self.desc

    def breakItem(self):
        if not self.isBroken:
            print("<Crash!>")
            self.desc = "broken " + self.desc
            self.isBroken = True

    def isUsable(self, player, target):
        if self.usableConditionTest:
            return self.usableConditionTest( player, target )
        else:
            return False

    def useItem(self, player, target):
        if self.useAction:
            self.useAction(player, self, target)

class OpenableItem(Item):
    def __init__(self, desc, contents=None):
        super(OpenableItem,self).__init__(desc)
        self.isOpenable = True
        self.isOpened = False
        if contents is not None:
            if isinstance(contents, Item):
                self.contents = [contents,]
            else:
                self.contents = contents
        else:
            self.contents = []

    def openItem(self, player):
        if not self.isOpened:
            self.isOpened = not self.isOpened
            if self.contents is not None:
                for item in self.contents:
                    player.room.addItem( item )
                self.contents = []
            self.desc = "open " + self.desc

    def closeItem(self, player):
        if self.isOpened:
            self.isOpened = not self.isOpened
            if self.desc.startswith("open "):
                self.desc = self.desc[5:]


class Command(object):
    "Base class for commands"
    def __init__(self, verb, verbProg):
        self.verb = verb
        self.verbProg = verbProg

    @staticmethod
    def helpDescription():
        return ""

    def _doCommand(self, player):
        pass

    def __call__(self, player ):
        print(self.verbProg.capitalize()+"...")
        self._doCommand(player)


class MoveCommand(Command):
    def __init__(self, quals):
        super(MoveCommand,self).__init__("MOVE", "moving")
        self.direction = quals.direction[0]

    @staticmethod
    def helpDescription():
        return """MOVE or GO - go NORTH, SOUTH, EAST, or WEST
          (can abbreviate as 'GO N' and 'GO W', or even just 'E' and 'S')"""

    def _doCommand(self, player):
        rm = player.room
        nextRoom = rm.doors[
            {
            "N":0,
            "S":1,
            "E":2,
            "W":3,
            }[self.direction]
            ]
        if nextRoom:
            player.moveTo( nextRoom )
        else:
            print("Can't go that way.")


class TakeCommand(Command):
    def __init__(self, quals):
        super(TakeCommand,self).__init__("TAKE", "taking")
        self.subject = quals.item

    @staticmethod
    def helpDescription():
        return "TAKE or PICKUP or PICK UP - pick up an object (but some are deadly)"

    def _doCommand(self, player):
        rm = player.room
        subj = Item.items[self.subject]
        if subj in rm.inv and subj.isVisible:
            if subj.isTakeable:
                rm.removeItem(subj)
                player.take(subj)
            else:
                print(subj.cantTakeMessage)
        else:
            print("There is no %s here." % subj)


class DropCommand(Command):
    def __init__(self, quals):
        super(DropCommand,self).__init__("DROP", "dropping")
        self.subject = quals.item

    @staticmethod
    def helpDescription():
        return "DROP or LEAVE - drop an object (but fragile items may break)"

    def _doCommand(self, player):
        rm = player.room
        subj = Item.items[self.subject]
        if subj in player.inv:
            rm.addItem(subj)
            player.drop(subj)
        else:
            print("You don't have %s." % (aOrAn(subj)))

class InventoryCommand(Command):
    def __init__(self, quals):
        super(InventoryCommand,self).__init__("INV", "taking inventory")

    @staticmethod
    def helpDescription():
        return "INVENTORY or INV or I - lists what items you have"

    def _doCommand(self, player):
        print("You have %s." % enumerateItems( player.inv ))

class LookCommand(Command):
    def __init__(self, quals):
        super(LookCommand,self).__init__("LOOK", "looking")

    @staticmethod
    def helpDescription():
        return "LOOK or L - describes the current room and any objects in it"

    def _doCommand(self, player):
        player.room.describe()

class DoorsCommand(Command):
    def __init__(self, quals):
        super(DoorsCommand,self).__init__("DOORS", "looking for doors")

    @staticmethod
    def helpDescription():
        return "DOORS - display what doors are visible from this room"

    def _doCommand(self, player):
        rm = player.room
        numDoors = sum([1 for r in rm.doors if r is not None])
        if numDoors == 0:
            reply = "There are no doors in any direction."
        else:
            if numDoors == 1:
                reply = "There is a door to the "
            else:
                reply = "There are doors to the "
            doorNames = [ {0:"north", 1:"south", 2:"east", 3:"west"}[i]
                          for i,d in enumerate(rm.doors) if d is not None ]
            #~ print doorNames
            reply += enumerateDoors( doorNames )
            reply += "."
            print(reply)

class UseCommand(Command):
    def __init__(self, quals):
        super(UseCommand,self).__init__("USE", "using")
        self.subject = Item.items[quals.usedObj]
        if quals.targetObj:
            self.target = Item.items[quals.targetObj]
        else:
            self.target = None

    @staticmethod
    def helpDescription():
        return "USE or U - use an object, optionally IN or ON another object"

    def _doCommand(self, player):
        rm = player.room
        availItems = rm.inv + player.inv
        if self.subject in availItems:
            if self.subject.isUsable( player, self.target ):
                self.subject.useItem( player, self.target )
            else:
                print("You can't use that here.")
        else:
            print("There is no %s here to use." % self.subject)

class OpenCommand(Command):
    def __init__(self, quals):
        super(OpenCommand,self).__init__("OPEN", "opening")
        self.subject = Item.items[quals.item]

    @staticmethod
    def helpDescription():
        return "OPEN or O - open an object"

    def _doCommand(self, player):
        rm = player.room
        availItems = rm.inv+player.inv
        if self.subject in availItems:
            if self.subject.isOpenable:
                if not self.subject.isOpened:
                    self.subject.openItem( player )
                else:
                    print("It's already open.")
            else:
                print("You can't open that.")
        else:
            print("There is no %s here to open." % self.subject)

class CloseCommand(Command):
    def __init__(self, quals):
        super(CloseCommand,self).__init__("CLOSE", "closing")
        self.subject = Item.items[quals.item]

    @staticmethod
    def helpDescription():
        return "CLOSE or CL - close an object"

    def _doCommand(self, player):
        rm = player.room
        availItems = rm.inv+player.inv
        if self.subject in availItems:
            if self.subject.isOpenable:
                if self.subject.isOpened:
                    self.subject.closeItem( player )
                else:
                    print("You can't close that, it's not open.")
            else:
                print("You can't close that.")
        else:
            print("There is no %s here to close." % self.subject)

class QuitCommand(Command):
    def __init__(self, quals):
        super(QuitCommand,self).__init__("QUIT", "quitting")

    @staticmethod
    def helpDescription():
        return "QUIT or Q - ends the game"

    def _doCommand(self, player):
        print("Ok....")
        player.gameOver = True

class HelpCommand(Command):
    def __init__(self, quals):
        super(HelpCommand,self).__init__("HELP", "helping")

    @staticmethod
    def helpDescription():
        return "HELP or H or ? - displays this help message"

    def _doCommand(self, player):
        print("Enter any of the following commands (not case sensitive):")
        for cmd in [
            InventoryCommand,
            DropCommand,
            TakeCommand,
            UseCommand,
            OpenCommand,
            CloseCommand,
            MoveCommand,
            LookCommand,
            DoorsCommand,
            QuitCommand,
            HelpCommand,
            ]:
            print("  - %s" % cmd.helpDescription())
        print()

class AppParseException(ParseException):
    pass

class Parser(object):
    def __init__(self):
        self.bnf = self.makeBNF()

    def makeBNF(self):
        invVerb = oneOf("INV INVENTORY I", caseless=True)
        dropVerb = oneOf("DROP LEAVE", caseless=True)
        takeVerb = oneOf("TAKE PICKUP", caseless=True) | \
            (CaselessLiteral("PICK") + CaselessLiteral("UP") )
        moveVerb = oneOf("MOVE GO", caseless=True) | empty
        useVerb = oneOf("USE U", caseless=True)
        openVerb = oneOf("OPEN O", caseless=True)
        closeVerb = oneOf("CLOSE CL", caseless=True)
        quitVerb = oneOf("QUIT Q", caseless=True)
        lookVerb = oneOf("LOOK L", caseless=True)
        doorsVerb = CaselessLiteral("DOORS")
        helpVerb = oneOf("H HELP ?",caseless=True)

        itemRef = OneOrMore(Word(alphas)).setParseAction( self.validateItemName )
        nDir = oneOf("N NORTH",caseless=True).setParseAction(replaceWith("N"))
        sDir = oneOf("S SOUTH",caseless=True).setParseAction(replaceWith("S"))
        eDir = oneOf("E EAST",caseless=True).setParseAction(replaceWith("E"))
        wDir = oneOf("W WEST",caseless=True).setParseAction(replaceWith("W"))
        moveDirection = nDir | sDir | eDir | wDir

        invCommand = invVerb
        dropCommand = dropVerb + itemRef("item")
        takeCommand = takeVerb + itemRef("item")
        useCommand = useVerb + itemRef("usedObj") + \
            Optional(oneOf("IN ON",caseless=True)) + \
            Optional(itemRef,default=None)("targetObj")
        openCommand = openVerb + itemRef("item")
        closeCommand = closeVerb + itemRef("item")
        moveCommand = moveVerb + moveDirection("direction")
        quitCommand = quitVerb
        lookCommand = lookVerb
        doorsCommand = doorsVerb
        helpCommand = helpVerb

        # attach command classes to expressions
        invCommand.setParseAction(InventoryCommand)
        dropCommand.setParseAction(DropCommand)
        takeCommand.setParseAction(TakeCommand)
        useCommand.setParseAction(UseCommand)
        openCommand.setParseAction(OpenCommand)
        closeCommand.setParseAction(CloseCommand)
        moveCommand.setParseAction(MoveCommand)
        quitCommand.setParseAction(QuitCommand)
        lookCommand.setParseAction(LookCommand)
        doorsCommand.setParseAction(DoorsCommand)
        helpCommand.setParseAction(HelpCommand)

        # define parser using all command expressions
        return ( invCommand |
                  useCommand |
                  openCommand |
                  closeCommand |
                  dropCommand |
                  takeCommand |
                  moveCommand |
                  lookCommand |
                  doorsCommand |
                  helpCommand |
                  quitCommand )("command") + LineEnd()

    def validateItemName(self,s,l,t):
        iname = " ".join(t)
        if iname not in Item.items:
            raise AppParseException(s,l,"No such item '%s'." % iname)
        return iname

    def parseCmd(self, cmdstr):
        try:
            ret = self.bnf.parseString(cmdstr)
            return ret
        except AppParseException as pe:
            print(pe.msg)
        except ParseException as pe:
            print(random.choice([ "Sorry, I don't understand that.",
                                   "Huh?",
                                   "Excuse me?",
                                   "???",
                                   "What?" ] ))

class Player(object):
    def __init__(self, name):
        self.name = name
        self.gameOver = False
        self.inv = []

    def moveTo(self, rm):
        self.room = rm
        rm.enter(self)
        if self.gameOver:
            if rm.desc:
                rm.describe()
            print("Game over!")
        else:
            rm.describe()

    def take(self,it):
        if it.isDeadly:
            print("Aaaagh!...., the %s killed me!" % it)
            self.gameOver = True
        else:
            self.inv.append(it)

    def drop(self,it):
        self.inv.remove(it)
        if it.isFragile:
            it.breakItem()


def createRooms( rm ):
    """
    create rooms, using multiline string showing map layout
    string contains symbols for the following:
     A-Z, a-z indicate rooms, and rooms will be stored in a dictionary by
               reference letter
     -, | symbols indicate connection between rooms
     <, >, ^, . symbols indicate one-way connection between rooms
    """
    # start with empty dictionary of rooms
    ret = {}

    # look for room symbols, and initialize dictionary
    # - exit room is always marked 'Z'
    for c in rm:
        if c in string.ascii_letters:
            if c != "Z":
                ret[c] = Room(c)
            else:
                ret[c] = Exit()

    # scan through input string looking for connections between rooms
    rows = rm.split("\n")
    for row,line in enumerate(rows):
        for col,c in enumerate(line):
            if c in string.ascii_letters:
                room = ret[c]
                n = None
                s = None
                e = None
                w = None

                # look in neighboring cells for connection symbols (must take
                # care to guard that neighboring cells exist before testing
                # contents)
                if col > 0 and line[col-1] in "<-":
                    other = line[col-2]
                    w = ret[other]
                if col < len(line)-1 and line[col+1] in "->":
                    other = line[col+2]
                    e = ret[other]
                if row > 1 and col < len(rows[row-1]) and rows[row-1][col] in '|^':
                    other = rows[row-2][col]
                    n = ret[other]
                if row < len(rows)-1 and col < len(rows[row+1]) and rows[row+1][col] in '|.':
                    other = rows[row+2][col]
                    s = ret[other]

                # set connections to neighboring rooms
                room.doors=[n,s,e,w]

    return ret

# put items in rooms
def putItemInRoom(i,r):
    if isinstance(r,str):
        r = rooms[r]
    r.addItem( Item.items[i] )

def playGame(p,startRoom):
    # create parser
    parser = Parser()
    p.moveTo( startRoom )
    while not p.gameOver:
        cmdstr = input(">> ")
        cmd = parser.parseCmd(cmdstr)
        if cmd is not None:
            cmd.command( p )
    print()
    print("You ended the game with:")
    for i in p.inv:
        print(" -", aOrAn(i))


#====================
# start game definition
roomMap = """
     d-Z
     |
   f-c-e
   . |
   q<b
     |
     A
"""
rooms = createRooms( roomMap )
rooms["A"].desc = "You are standing on the front porch of a wooden shack."
rooms["b"].desc = "You are in a garden."
rooms["c"].desc = "You are in a kitchen."
rooms["d"].desc = "You are on the back porch."
rooms["e"].desc = "You are in a library."
rooms["f"].desc = "You are on the patio."
rooms["q"].desc = "You are sinking in quicksand.  You're dead..."
rooms["q"].gameOver = True

# define global variables for referencing rooms
frontPorch = rooms["A"]
garden     = rooms["b"]
kitchen    = rooms["c"]
backPorch  = rooms["d"]
library    = rooms["e"]
patio      = rooms["f"]

# create items
itemNames = """sword.diamond.apple.flower.coin.shovel.book.mirror.telescope.gold bar""".split(".")
for itemName in itemNames:
    Item( itemName )
Item.items["apple"].isDeadly = True
Item.items["mirror"].isFragile = True
Item.items["coin"].isVisible = False
Item.items["shovel"].usableConditionTest = ( lambda p,t: p.room is garden )
def useShovel(p,subj,target):
    coin = Item.items["coin"]
    if not coin.isVisible and coin in p.room.inv:
        coin.isVisible = True
Item.items["shovel"].useAction = useShovel

Item.items["telescope"].isTakeable = False
def useTelescope(p,subj,target):
    print("You don't see anything.")
Item.items["telescope"].useAction = useTelescope

OpenableItem("treasure chest", Item.items["gold bar"])
Item.items["chest"] = Item.items["treasure chest"]
Item.items["chest"].isTakeable = False
Item.items["chest"].cantTakeMessage = "It's too heavy!"

OpenableItem("mailbox")
Item.items["mailbox"].isTakeable = False
Item.items["mailbox"].cantTakeMessage = "It's nailed to the wall!"

putItemInRoom("mailbox", frontPorch)
putItemInRoom("shovel", frontPorch)
putItemInRoom("coin", garden)
putItemInRoom("flower", garden)
putItemInRoom("apple", library)
putItemInRoom("mirror", library)
putItemInRoom("telescope", library)
putItemInRoom("book", kitchen)
putItemInRoom("diamond", backPorch)
putItemInRoom("treasure chest", patio)

# create player
plyr = Player("Bob")
plyr.take( Item.items["sword"] )

# start game
playGame( plyr, frontPorch )
