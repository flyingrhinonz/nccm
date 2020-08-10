#!/usr/bin/python3

'''
NCurses ssh Connection Manager (nccm)
=====================================

Copyright (C) 2020 Kenneth Aaron.

Freedom makes a better world: released under GNU GPLv3.
https://www.gnu.org/licenses/gpl-3.0.en.html

Free for personal use (as in "at home").

Free for all non-personal use (organizational,
non-profit, government, education, commercial, etc) -
please send me email if this software is useful to your
organization.

flyingrhino AT orcon DOT net DOT nz

This software can be used by anyone at no cost, however
if you can support - please donate money to a
children's hospital of your choice.

This program is free software: you can redistribute it
and/or modify it under the terms of the GNU General Public
License as published by the Free Software Foundation:
GNU GPLv3. You must include this entire text with your
distribution.

This program is distributed in the hope that it will be
useful, but WITHOUT ANY WARRANTY; without even the implied
warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
PURPOSE.
See the GNU General Public License for more details.


Manual install instructions
---------------------------

Copy the script to a directory of your choice and prepare
the ssh connections yml file in one of the supported
directories.

You may need to manually install the PyYAML module:
  pip3 install --user PyYAML

You may even need to install the python pip3 program if
your distro doesn't have it.

You can do the following:
  copy the nccm.py script to: /usr/local/bin/
  cd /usr/local/bin/
  chmod 755 nccm.py
  chown root:root nccm.py

The script can then be run by simply typing 'nccm.py'
from anywhere.

The ssh connections (servers) file is loaded from the
following paths, whichever is found first:
  ~/.config/nccm/nccm.yml
  ~/.nccm.yml
  ~/nccm.yml
  /etc/nccm.yml

This program comes with an example yml file. Edit it
so suit your needs.


Controls
--------

Up/Down arrows      Scroll the list up/down
Home/End            Jump to list first/last entry
PgUp/PgDn           Page up/down in the list
Shift Up/Down       Move the marker up/down
Shift Left/Right    Move the marker to display top/bottom
Enter               Connect to the selected entry

Ctrl-h              Display this help menu
Ctrl-q or Ctrl-c    Quit the program
F1-F4 or !@#$       Sort by respective column (1-4)


Usage
-----

'Conn #' textbox:
Accepts integer values only (and !@#$ for sorting).
Pressing Enter here will connect to this connection ID,
(provided it is a valid connection number in the full
(unfiltered) connections list), ignoring everything else:
Filter textbox, highlighted line - even if they don't
match. If this textbox is empty, it will connect to the
connection marked by the highlighted line.

'Filter:' textbox:
Type any filter text here.
Accepts any printable character and space.
Text is forced to lowercase, and the resulting filtering
is case insensitive.
Pressing Enter will connect to the connection highlighed
in red. This also works if you're in the Conn textbox
and it's empty.

Textboxes accept backspace to delete one char backwards,
inline editing not supported.

Displayed connection list is filtered by the combined
contents of all the fields as you type in real time.
Spaces delimit filters if typed into 'Filter:' textbox
and all filter entries are AND'ed.

Regular direction keys (arrow up/down, home, end, pgup,
pgdn) scroll the list vertically.
Arrow left/right scroll the list horizontally if the text
is longer than the width of your window.
Shift arrow up/down scrolls the marker up/down within the
confines of your display. Shift arrow left/right jumps
the marker to the first/last visible line in your display.
The reason for doing it this way is that independant
list and marker movement usually achieves faster results
with less keypresses.


Sorting
-------

F1-F4 keys sort by the respective fields 1-4.
The Fn keys may be captured by certain GUIs so we have
an alternative - when focused on 'Conn #' window, press
shift-1 through 4 (!@#$) to toggle sorting by the
respective field number.
Pressing the same key again reverses the sort order.


Limitations
-----------

Lots...

Will not store passwords. Please don't request this
feature because it won't be added.
Either use ssh passwordless login (by placing your
public key on the server in .ssh/authorized_keys - tip:
look up ssh-copy-id) or store your password in a
password manager and paste it when prompted.

Does not like window resizing and display will do
strange things. Upsizing the window usually messes
up the screen, while downsizing the window throws
an exception.
If things go wrong, and you're still stuck in the window,
exit with ctrl-q or ctrl-c and run it again.
It's safe to resize the window once connection
establishment is in progress or after connected to
your server.

Does not support highlighting filter keywords in search
results because this results in a messy and confusing
display once more than a couple keywords are used.

Text entry is limited to the length of the textboxes
which in turn are dictated by the width of your window.
This should be enough for most use cases though.


Misc
----

This program aims to do one thing well - let you make SSH
connections from an ncurses based manager with minimum
distraction. I wish to avoid feature creep to keep it
on focus.

The code is heavily commented, with the hope that it will
make life easier for modders and forkers.

'''

# Standard library imports:
import collections
import curses
import itertools
import operator
import os.path
import pathlib
import pydoc
import shlex
import string
import subprocess

# Pay attention to these imports:
import yaml         # Requires: 'pip3 install --user PyYAML'


QuitAfterSsh = True     # Quit this program after ssh connection is completed

# Setup the supported directories/pathnames for the connections file:
ConfigFile = 'nccm.yml'
ConfigFilePath = []
ConfigFilePath.append(str(pathlib.Path.home()) + '/.config/nccm/' + ConfigFile)
ConfigFilePath.append(str(pathlib.Path.home()) + '/.' + ConfigFile)
ConfigFilePath.append(str(pathlib.Path.home()) + '/' + ConfigFile)
ConfigFilePath.append('/etc/' + ConfigFile)

ScreenHeight = ScreenWidth = 0      # The terminal window dimensions
DisplayObjects = []     # A list of window objects that display info on the screen (no user input)
TextboxObjects = []     # A list of editable textbox windows (user input)

HelpMenuItems = collections.OrderedDict((
    ( 'Arrows', 'Scroll' ),
    ( 'Enter', 'Select' ),
    ( 'ctrl-h', 'Help' ),
    ( 'ctrl-q', 'Quit' ),
))

ConnectionsFileHeaderText = '''# Servers configuration file in YAML format.
# Use the following format:
#   FRIENDLY_NAME:
#     address: SERVER_ADDRESS
#     comment: FREETEXT_COMMENT
#     user: USER_NAME
#
#   Details:
#       FRIENDLY_NAME - Can be any freetext descriptive name (recommended field)
#       SERVER_ADDRESS - Hostname or IP address (mandatory field)
#       FREETEXT_COMMENT - Any freetext you like to store as a comment on this connection (optional field)
#       USER_NAME - Your login name (mandatory field)
'''

ExampleServers = {
        'border router':
            { 'user': 'admin', 'address': '192.168.1.1', 'comment': 'My border router', },
        'test server':
            { 'user': 'root', 'address': 'test.example.com', },
        'Another server':
            { 'user': 'foo', 'address': '10.2.2.2', 'comment': 'this is another comment', },
}


class HelpTextDisplay:
    ''' This manages window objects for help lines '''

    def __init__(self, LinesCount=None, ColsCount=None,
        BeginY=None, BeginX=None):
        self.Window = curses.newwin(LinesCount, ColsCount, BeginY, BeginX)

        for Looper in HelpMenuItems:
            self.Window.addstr('  '+Looper, curses.color_pair(1))
            self.Window.addstr('-'+HelpMenuItems[Looper], curses.color_pair(2))

    def Display(self):
        self.Window.noutrefresh()


class BasicTextDisplay:
    ''' This manages window objects to display simple text '''

    def __init__(self, LinesCount=None, ColsCount=None,
        BeginY=None, BeginX=None, Text='', ColorPair=0):
        self.Window = curses.newwin(LinesCount, ColsCount, BeginY, BeginX)
        self.Window.addstr(Text, curses.color_pair(ColorPair))

    def Display(self):
        self.Window.noutrefresh()


class Connections:
    ''' This handles the connections list.

        TextFilters are the objects that hold user input (the textboxes) so that we can
            later filter the display with text from them (Display method).
        '''

    def __init__(self, LinesCount=None, ColsCount=None, BeginY=None,
        BeginX=None, ColorPair=0, TextFilters=None):

        # Window parameters:
        self.ColorPair = ColorPair
        self.TextFilters = TextFilters
        self.MaxTextLines = LinesCount-1
        self.MaxTextWidth = ColsCount-2

        # Storage components:
        self.LoadedServersDict = {}
            # ^ The yaml connections file loaded into a dict. Apart from conversion to
            #   internal formats, this dict won't be used again.
        self.FullServersList = []
            # ^ Full list as imported from the loaded object
            #   This is the source list that we reuse during the program.
            #   It is also sorted in place if the user chooses sorting by column.
        self.MaxLenCounter = 0      # Length of the longest serial number field
        self.MaxLenFriendly = 0     # Length of the longest friendly name
        self.MaxLenCommand = 0      # Length of the longest connection string command (root@server)
        self.MaxLenComment = 0      # Length of the longest comment column

        self.SortOrder = True       # Column sort order (flips between True/False)
        self.YOffset = 0            # Y offset for scrolling vertically
        self.XOffset = 0            # X offset for scrolling horizontally
        self.MaxLineLength = 0      # Result of formatting the text to fit the max column length
        self.MarkerLine = 0         # Highlighted line for connection selection
        self.SelectedEntry = None   # The connection number matching MarkerLine
        self.SelectedEntryVal = None    # Connection number value of the highlighted line
        self.DisplayResultsCount = 0    # Number of displayed results after filtering

        self.Window = curses.newwin(LinesCount, ColsCount, BeginY, BeginX)


    def Load(self):
        ''' Loads the connections file '''

        for FileLooper in ConfigFilePath:
            if os.path.exists(FileLooper):
                break

        with open (FileLooper, 'r') as ConfigFileToRead:
            self.LoadedServersDict = yaml.safe_load(ConfigFileToRead)    # yaml.load is not safe

        # Populate the FullServersList (list of config items as lists, even unconfigured items):
        for Counter, Item in enumerate(sorted(self.LoadedServersDict.keys(), key=str.lower)):
            UserName = self.LoadedServersDict[Item].get('user', '')
            Address = self.LoadedServersDict[Item].get('address', '')
            Comment = self.LoadedServersDict[Item].get('comment', '')
                # ^ .get because item my be empty
            self.FullServersList.append([
                Counter, Item, '{}@{}'.format(UserName, Address), Comment])
         # ^ Now we have a list of lists:
         #  [[Serial # , FriendlyName , ConnString , Comment] , [...]]

        # Calculate the max length of each column:
        for Counter, Looper in enumerate([
            'MaxLenCounter', 'MaxLenFriendly', 'MaxLenCommand', 'MaxLenComment']):
            setattr(self, Looper, max(len(str(i[Counter])) for i in self.FullServersList))


    def Sort(self, Column):
        ''' Sorts the internal-use FullServersList list per the requested column '''

        self.FullServersList.sort(key=operator.itemgetter(Column), reverse=self.SortOrder)
        self.SortOrder = not(self.SortOrder)
            # ^ Reverse True to False, False to True so that next time this function
            #   is called the sort will be reversed.


    def Save(self):
        ''' Saves the connections file '''
        # Nothing here. Might add save feature if I allow user to add connection details


    def SaveExample(self):
        ''' Saves an example of the connections file to the current directory.
            You can move it later to one of the directory options listed in the
            main docstring.
            Use this if you want to create a clean connections file that you can later edit.
            It is saved in yaml format.
        '''

        with open (ConfigFile, 'w') as ConfigFileToWrite:
                # ^ First time "w" so we overwrite the file
            print(ConnectionsFileHeaderText, file=ConfigFileToWrite)
            yaml.dump(ExampleServers, ConfigFileToWrite)

        print('Clean example connections file saved to: {}'.format(ConfigFile))


    def Connect(self, Counter):
        ''' Make ssh connection '''

        Counter = int(Counter)

        SshCommand = 'ssh ' + [ i[2] for i in self.FullServersList if i[0] == Counter ][0]
        print('About to ssh to: {} ...'.format(SshCommand))
        ExtCommand = shlex.split(SshCommand)    # Split the command line into arguments
        subprocess.run(ExtCommand)              # Connect to the ssh server
        print('Completed ssh to: {} ...'.format(SshCommand))


    def Display(self):

        FilterTextList = set()          # Unique text strings for filtering
        self.ResultsList = []           # Result of the filtering

        self.Window.erase()

        # Merge the users text input into a set whose uniqueness improves search performance:
        for Looper in self.TextFilters:
            FilterTextList.update(set(Looper.Text.split(' ')))

        # Populate self.ResultsList with all line that match the above filter:
        for Counter, LineLooper in enumerate(self.FullServersList):
            Line = ('{:<{CounterWidth}}    {:<{ItemWidth}}    '
                '{:<{CommandWidth}}    {:<{CommentWidth}}'
                 .format(
                    LineLooper[0],
                    LineLooper[1],
                    LineLooper[2],
                    LineLooper[3],
                    CounterWidth = self.MaxLenCounter,
                    ItemWidth = self.MaxLenFriendly,
                    CommandWidth = self.MaxLenCommand,
                    CommentWidth = self.MaxLenComment))

            if len(Line) > self.MaxLineLength:
                self.MaxLineLength = len(Line)

            if sorted(FilterTextList) == sorted(x for x in FilterTextList if x in Line):
                self.ResultsList.append(Line)

        self.ResultsList = [x.ljust(self.MaxLineLength, ' ') for x in self.ResultsList]
        self.DisplayResultsCount = 0

        if self.MarkerLine > (len(self.ResultsList)-1):
            self.MarkerLine = (len(self.ResultsList)-1)
        if self.MarkerLine < 0:
            self.MarkerLine = 0
        self.SelectedEntry = None

        for LineNumber, Looper in enumerate(
            self.ResultsList[self.YOffset:(self.YOffset+self.MaxTextLines)]):
            self.DisplayResultsCount += 1   # Number of lines displayed
            PaddedString = Looper[self.XOffset:(self.XOffset+self.MaxTextWidth)]

            if LineNumber == self.MarkerLine:
                self.Window.addstr(PaddedString, curses.color_pair(4))
                self.SelectedEntry = Looper
                self.SelectedEntryVal = int(self.SelectedEntry.lstrip().split()[0])
            else:
                self.Window.addstr(PaddedString)

            self.Window.addstr('\n')

        self.Window.noutrefresh()


class TextBox:
    ''' This manages objects that handle text input '''

    def __init__(self, LinesCount=None, ColsCount=None,
        BeginY=None, BeginX=None, ColorPair=0):

        self.Text = ''  # This is the text that the user enters
        self.MaxText = ColsCount-1
        self.Window = curses.newwin(LinesCount, ColsCount, BeginY, BeginX)
        self.Window.keypad(True)
            # ^ Get special keys support for this window.
            #   Calling 'stdscr.keypad(True)' is different and doesn't reflect in windows -
            #   it must be called separately.
            #   Very important - otherwise stuff like getch return stuff like arrow keys
            #   in multiple bytes (one per call) and it's screwed up.
        self.Window.bkgd(' ', curses.color_pair(ColorPair))


    def Display(self):
        self.Window.noutrefresh()


    def ZeroCursor(self):
        ''' Position the cursor at 0, 0 in this window.
            Call with:
                ConnBox.ZeroCursor()
        '''

        self.Window.move(0, 0)      # Position cursor at 0, 0


    def ActivateWindow(self):
        ''' Brings this window to the front.
            Call with:
                ConnBox.ActivateWindow()
        '''

        self.Window.noutrefresh()
        curses.doupdate()


    def ReadKey(self):
        UserKey = self.Window.getch()    # Read a key and return a code
        return UserKey


    def ProcessKey(self, Key):

        if Key == curses.KEY_BACKSPACE or Key == 263:   # Backspace key
            if len(self.Text) > 0:
                self.Text = self.Text[:-1]

        elif len(self.Text) < self.MaxText:
            self.Text += chr(Key).lower()
                # ^ Force to lower and search is case insensitive

        self.Window.clear()
        self.Window.addstr(0, 0, self.Text)


def RestoreTerminal(stdscr):
    ''' Restore the terminal to a sane status '''

    curses.curs_set(1)          # Restore blinking cursor
    curses.echo()               # Restore terminal echo
    stdscr.keypad(False)        # Return special keys to normal
    curses.noraw()              # Return raw mode to normal
    curses.endwin()             # End curses session


def UpdateDisplay():
    ''' The window objects were added to DisplayObjects list, so here we need to use the
        Display method of those objects. '''

    global DisplayObjects

    for Looper in DisplayObjects:
        Looper.Display()
    curses.doupdate()   # Speed up display and avoid flickering by using 'window.noutrefresh'


def SetupCurses(stdscr):
    ''' Put all pre-run tests here. Any failure will exit the program. '''


    global ScreenHeight, ScreenWidth

    curses.curs_set(1)          # Enable the blinking cursor
    curses.noecho()             # Disable echo to the terminal
    stdscr.keypad(True)
        # ^ Get special keys support in stdscr. Per window setting also required
    curses.raw()                # Disable control codes

    curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_RED)

    if not curses.has_colors(): # Color not supported
        RestoreTerminal(stdscr)
        print('This program requires color support')
        return False

    ScreenHeight, ScreenWidth = stdscr.getmaxyx()

    if ScreenWidth < 60 or ScreenHeight < 15:
        RestoreTerminal(stdscr)
        print('Window must be at least 60x15')
        return False


def SetupWindows():
    ''' Create the various windows '''

    global ScreenHeight, ScreenWidth
    global DisplayObjects
    global TextboxObjects

    # Help text display window:
    HelpBox = HelpTextDisplay(LinesCount=1, ColsCount=ScreenWidth,
        BeginY=ScreenHeight-1, BeginX=0)
    DisplayObjects.append(HelpBox)      # Add this window to the displayable windows

    # Connection text display window:
    ConnText = BasicTextDisplay(LinesCount=1, ColsCount=10,
        BeginY=ScreenHeight-3, BeginX=2, Text='Conn #', ColorPair=1)
    DisplayObjects.append(ConnText)

    # Connection text input window:
    ConnBox = TextBox(LinesCount=1, ColsCount=8,
        BeginY=ScreenHeight-3, BeginX=10, ColorPair=3)
    DisplayObjects.append(ConnBox)      # Add this window to the displayable windows
    TextboxObjects.append(ConnBox)      # Add this window to the windows that store user input
                                        # ^ We do this because later we filter the ConnectionsList
                                        #   display output based upon the text here.

    # Filter text display window:
    FilterText = BasicTextDisplay(LinesCount=1, ColsCount=10,
        BeginY=ScreenHeight-3, BeginX=20, Text='Filter:', ColorPair=1)
    DisplayObjects.append(FilterText)

    # Filter text input window:
    FilterBox = TextBox(LinesCount=1, ColsCount=ScreenWidth-31,
        BeginY=ScreenHeight-3, BeginX=29, ColorPair=3)
    DisplayObjects.append(FilterBox)
    TextboxObjects.append(FilterBox)

    # Connections list text display window:
    ConnectionsList = Connections(LinesCount=ScreenHeight-3,
        ColsCount=ScreenWidth, BeginY=0, BeginX=0, ColorPair=0,
        TextFilters=[FilterBox, ConnBox])
    #ConnectionsList.SaveExample()
        # ^ Uncomment this line to create a clean example connections file
        #   which will be saved to the current directory.
    ConnectionsList.Load()
        # ^ Load the connections list config file into this object (normal operation)
    DisplayObjects.append(ConnectionsList)

    CyclicTextboxObjects = itertools.cycle(TextboxObjects)
        # ^ Call this after adding all the textbox windows
        #   We will use it as a cyclic list iterator so that every press of TAB
        #   will give us the next textbox object in the list.

    return ConnectionsList, ConnBox, FilterBox, CyclicTextboxObjects


def MainCursesFunction(stdscr):

    if SetupCurses(stdscr) == False:       # Something failed in setup or tests
        return

    ConnectionsList, ConnBox, FilterBox, CyclicTextboxObjects = SetupWindows()
    UpdateDisplay()
    ActiveWindow = FilterBox    # The first window to read user input from
    FilterBox.ZeroCursor()
        # ^ We have no input text so activate ConnBox window and zero the cursor.
        #   Failure to do this will position the cursor at the last window drawn.

    # This block loops in the CyclicTextboxObjects until it's positioned at ActiveWindow.
    # We need this because the initial starting point may not be correct and the first
    # time we press TAB may do nothing:
    for Looper in CyclicTextboxObjects:
        if Looper == ActiveWindow:
            break

    while True:
        UserKey = ActiveWindow.ReadKey()

        if UserKey == -1:       # Happens when window is resized
            # ^ If I don't capture this, window resize causes a curses exception
            pass

        elif UserKey == 9:    # Tab key
            ActiveWindow = next(CyclicTextboxObjects)
                # ^ See the 'for Looper in CyclicTextboxObjects:' comment above
            ActiveWindow.ActivateWindow()
                # ^ Get the next item in the iterable and run it's ActivateWindow method.
                #   This is effectively the next textbox window object

        elif ( (chr(UserKey) in string.digits
            or chr(UserKey) in string.ascii_letters
            or chr(UserKey) in string.punctuation
            or UserKey == 32        # Space
            or UserKey == curses.KEY_BACKSPACE
            or UserKey == 263)      # Backspace key
            and ActiveWindow == FilterBox ):
            # ^ Filterbox accepts any printable character or backspace
            #   Using string.punctuation crashes on ctrl-j input so I explictly
            #   identify the characters accepted.
                ConnectionsList.YOffset = 0
                ConnectionsList.XOffset = 0
                    # ^ Keypress received so reset the display to the beginning of the list
                ActiveWindow.ProcessKey(UserKey)

        elif ( (chr(UserKey) in string.digits
            or UserKey == curses.KEY_BACKSPACE
            or UserKey == 263)              # Backspace key
            and ActiveWindow == ConnBox ):
            # ^ Filterbox accepts any digit or backspace
                ActiveWindow.ProcessKey(UserKey)

        elif ( UserKey == 33                # ! key
            and ActiveWindow == ConnBox ):
                ConnectionsList.Sort(0)

        elif ( UserKey == 64                # @ key
            and ActiveWindow == ConnBox ):
                ConnectionsList.Sort(1)

        elif ( UserKey == 35                # # key
            and ActiveWindow == ConnBox ):
                ConnectionsList.Sort(2)

        elif ( UserKey == 36                # $ key
            and ActiveWindow == ConnBox ):
                ConnectionsList.Sort(3)

        elif UserKey == 337:                # Shift up arrow
            if ConnectionsList.MarkerLine > 0:
                ConnectionsList.MarkerLine -= 1

        elif UserKey == 336:                # Shift down arrow
            if ConnectionsList.MarkerLine < (ConnectionsList.DisplayResultsCount-1):
                ConnectionsList.MarkerLine += 1

        elif UserKey == 393:                # Shift left arrow
            ConnectionsList.MarkerLine = 0

        elif UserKey == 402:                # Shift right arrow
            ConnectionsList.MarkerLine = (ConnectionsList.DisplayResultsCount-1)

        elif UserKey == curses.KEY_UP:      # Up arrow
            if ConnectionsList.YOffset > 0:
                ConnectionsList.YOffset -= 1

        elif UserKey == curses.KEY_DOWN:    # Down arrow
            if len(ConnectionsList.ResultsList) - ConnectionsList.YOffset > ConnectionsList.MaxTextLines:
                ConnectionsList.YOffset += 1

        elif UserKey == curses.KEY_HOME:    # Home key
            ConnectionsList.YOffset = 0

        elif UserKey == curses.KEY_END:     # End key
            if len(ConnectionsList.ResultsList) > ConnectionsList.MaxTextLines:
                ConnectionsList.YOffset = len(ConnectionsList.ResultsList) - ConnectionsList.MaxTextLines

        elif UserKey == curses.KEY_PPAGE:   # PageUp key
            ConnectionsList.YOffset -= ConnectionsList.MaxTextLines
            if ConnectionsList.YOffset < 0:
                ConnectionsList.YOffset = 0

        elif UserKey == curses.KEY_NPAGE:   # PageDown key
            ConnectionsList.YOffset += ConnectionsList.MaxTextLines
            if ConnectionsList.YOffset > (len(ConnectionsList.ResultsList)-ConnectionsList.MaxTextLines):
                ConnectionsList.YOffset = len(ConnectionsList.ResultsList) - ConnectionsList.MaxTextLines

        elif UserKey == curses.KEY_LEFT:    # Left arrow
            ConnectionsList.XOffset -= (ConnectionsList.MaxTextWidth //3)
            if ConnectionsList.XOffset < 0:
                ConnectionsList.XOffset = 0

        elif UserKey == curses.KEY_RIGHT:   # Right arrow
            ConnectionsList.XOffset += (ConnectionsList.MaxTextWidth //3)
            if ConnectionsList.XOffset > (ConnectionsList.MaxLineLength - ConnectionsList.MaxTextWidth):
                ConnectionsList.XOffset = (ConnectionsList.MaxLineLength - ConnectionsList.MaxTextWidth)

        elif UserKey == 265:                # F1 key
            ConnectionsList.Sort(0)

        elif UserKey == 266:                # F2 key
            ConnectionsList.Sort(1)

        elif UserKey == 267:                # F3 key
            ConnectionsList.Sort(2)

        elif UserKey == 268:                # F4 key
            ConnectionsList.Sort(3)

        elif ((UserKey == curses.KEY_ENTER or UserKey in [10, 13])  # Enter key
            and ActiveWindow == ConnBox
            and ConnBox.Text):
                if (int(ConnBox.Text) >= 0
                    and int(ConnBox.Text) <= (len(ConnectionsList.FullServersList) -1)):
                        curses.endwin()
                        ConnectionsList.Connect(ConnBox.Text)
                        if QuitAfterSsh:        # Exit this program after ssh connection completed
                            break
                        else:
                            input('Press enter to return to nccm ...')

        elif ((UserKey == curses.KEY_ENTER or UserKey in [10, 13])
            and ConnectionsList.SelectedEntry):  # Enter key
                curses.endwin()
                ConnectionsList.Connect(ConnectionsList.SelectedEntryVal)
                if QuitAfterSsh:        # Exit this program after ssh connection completed
                    break
                else:
                    input('Press enter to return to nccm ...')

        elif UserKey == 8:      # Ctrl-h key
            curses.endwin()     # De-initialize and return terminal to normal status
            pydoc.pipepager(__doc__, cmd='less -i --dumb --no-init')
                # ^ Print the text in through the less pager
                #   so we can get paging, search, etc

        elif UserKey == 17 or UserKey == 3:     # ctrl-q / ctrl-c
            break

        UpdateDisplay()
        ActiveWindow.ActivateWindow()

    RestoreTerminal(stdscr)


def main(*args):
    curses.wrapper(MainCursesFunction)


if __name__ == '__main__':
        main()

