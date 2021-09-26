
NCurses ssh Connection Manager (nccm)
=====================================

![](images/program_screenshot.png)

Copyright (C) 2020-2021 Kenneth Aaron.

flyingrhino AT orcon DOT net DOT nz

Freedom makes a better world: released under GNU GPLv3.

https://www.gnu.org/licenses/gpl-3.0.en.html

This software can be used by anyone at no cost, however,
if you like using my software and can support - please
donate money to a children's hospital of your choice.

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


About nccm
----------

* Simple yet powerful ncurses ssh connection manager.
* Well documented.
* Secure.
* Logs are in English - you don't need to be a developer to
  read the majority of the logs.


Manual install instructions
---------------------------

This is the easiest way to install nccm, you can of course
install and use nccm in any way you wish.

* Clone the project from the git repository:
  `git clone https://github.com/flyingrhinonz/nccm nccm.git`
* `cd nccm.git/nccm/`
* `sudo install -m 755 nccm -t /usr/local/bin/`


The ssh connections/config file `nccm.yml` should be
copied to any one of the following locations, and is
loaded from the first location found in the following order:
- `~/.config/nccm/nccm.yml`
- `~/.nccm.yml`
- `~/nccm.yml`
- `/etc/nccm.yml`


Tips on nccm.yml location - if you're a single user then
placement of nccm.yml doesn't matter and it's probably
easiest to place it in one of the home dir locations.
In a multiuser system, placing nccm.yml in each user's
home dir will allow each user to use their personalized
settings if nccm.yml is present, and if not present then
fallback to default settings from /etc/nccm.yml.
It is also possible to put your real nccm.yml anywhere
you wish and make a symlink to it from one of the paths
mentioned above.
Also refer to  `nccm_config_importnccmd` setting which
allows you to import and merge connection details from
/etc/nccm.d/ .


nccm requires Python3 to be installed on your machine,
which should already be present on most Linux boxes.
Most Python library dependencies are already present
as part of Python3 however the following may not be
present in which case you need to install them manually.


On Debian or similar use apt:
If you want to only use the distro's packages you can do:
* `sudo apt install python3-yaml yamllint`

Or if you prefer to install PyYAML from pip3:
* `sudo apt install python3-pip yamllint`
* `pip3 install --user PyYAML`

On Fedora or similar use dnf:
* `sudo dnf install python3-pip yamllint`
* `pip3 install --user PyYAML`

Before starting, edit the `nccm.yml` file and add your
own ssh connections. Formatting YAML is easy and the file
you downloaded from the project page is well documented
and has examples of every supported scenario.
Follow the structure in the file - provide the connection
name at the beginning of a line and sub config items
indented by two spaces. Every subsequent nesting level
gets a further indent of two spaces. Don't forget the
colons - these are part of the YAML language.

Don't worry about ordering your SSH session blocks in any
specific way because nccm gives you "sort by" options
within the program as well as filtering.

Once you've finished editing, check your work with yamllint:
* `yamllint nccm.yml`

If no errors are returned, then you've formatted your file
correctly, and it's safe to continue.

If nccm is accessible from your path and is executable,
typing nccm is all that's required to launch the TUI
(terminal user interface).
If you see Python 3 exceptions, check whether you have
satisfied the dependencies. Any exceptions should mention
any package that's missing.


nccm.yml settings
-----------------

This file is mostly used for ssh connection details, but
also supports program settings as follows.

These are global settings, affecting all sessions.

`nccm_config_controlmode`:
Controls the cursor movement mode. Two modes are supported:
- std:    Cursor keys move the marker as expected.
- focus:  Marker and list move independently.
          The list is designed to move while the marker
          remains fixed unless it is moved manually.

`nccm_config_loglevel`:
Controls log level of messages sent by nccm to syslog.
If you are using systemd it usually captures syslog
messages which you can read in `journalctl`. I will use
the word syslog in this documentation as referral to both.
Use this for debugging. Default level is warning.
Supported levels: debug, info, warning, error, critical .

`nccm_config_logprivateinfo`:
Controls whether you want syslog/journal to include private
information such as usernames & hostnames. By default this
is set to `false` which results in the data being replaced
with `CENSORED` in the logs. Note - you will still see
`CENSORED` items for all lines that are logged before this
setting has been read from nccm.yml .
You can also force this temporarily by supplying the
command line argument:  `--logprivateinfo` .
This also solves the problem of censored logs that occur
before the `nccm_config_logprivateinfo` setting is loaded.
When this is enabled you will see:  `LogPrv` in red in the
help line at the bottom of the screen.

`nccm_config_keepalive`:
Sends a message through the encrypted channel every
n seconds (0 to disable) to prevent idle sessions from
being disconnected.
You can customize this on a per-connection basis by using
the setting `keepalive: n` (optional).

`nccm_config_identity`
For public key authentication, normally ssh will load your
private key from the default locations. You can force ssh
to use your own file by putting it's path here. Or set to
`false` to let ssh do it's own thing.
You can customize this on a per-connection basis by using
the setting `identity: path` (optional).

`nccm_config_sshprogram`
By default nccm will use the ssh program as found in your
path. If you want to explicitly set the path to ssh, or
you want to use a different program - set it here.
This is a global setting that affects all your connections.

`nccm_config_promptuser`
By default set to `false` and nccm will connect immediately
to the selected server. Set this value to `true`
if you want nccm to prompt the user to press Enter before
a connection is made.

`nccm_config_importnccmd:`
This setting defines whether nccm should try to import any
yml files it finds in /etc/nccm.d/ . Useful in a multiuser
env where each user can have their own nccm.yml as well as
shared connection details files. These filenames should end
in .yml and can only contain connection details without any
program settings.
As files are imported - older data will be updated with
newer data/values.
Note - nccm.yml from one of the supported directories is
loaded first, then /etc/nccm.d/*.yml are imported.

`nccm_config_logpath`
If you want nccm to save a copy of ssh terminal output
using `tee` - set this to the logfile path.
If this dir is missing, nccm will log an error and exit -
either fix the logging or disable it. The reasoning is that
you have logging on for a reason (either checking it later
or audit, etc) and it's better to know that logging is not
working now rather than doing your work and later finding
out that you don't have a log file.
The log filename format is:
{DATE}_{TIME}_{USER}_AT_{SERVER}_{SCREENWIDTH}x{SCREENHEIGHT}.nccm.log
Note - the screen dimensions are those when nccm started
the connection - they might have changed later on during
your session.
When tee logging is enabled you will see:  `LogTee`  in
white in the help line at the botton of the screen.

To view the resulting file I recommend using `catstep`
which can replay the file slowly and also let you step
through it at your own pace - it is available on my
github page: https://github.com/flyingrhinonz/catstep .
You can also use the regular Linux `cat` program but the
output will fly by really fast.

`nccm_loop_nccm`
Run nccm in a loop - when you exit out of your ssh session
nccm menu will reappear. You are allowed to resize your
window outside nccm and the new window size will apply when
nccm menu reappears after you exit from your ssh session.

`nccm_keybindings`
nccm is configured for US keyboard mapping as entered into
a standard linux xterm. If you have something else and
certain keys don't behave as you'd expect - change their
codes here.
I have experienced putty sending Home / End / Fn keys
differently to xterm - and other programs may have similar
behavior. You have the option of fixing your terminal
program or modifying the key codes within nccm.
Each of the keyboard codes is a list (even if it contains
only one item), you can map a keypress to as many codes as
you wish by adding more codes to it.
If you want to figure out what code results from a
keypress - run 'nccm -d' , press a key and look for:
'Keyboard entry: UserKey == nnn'  in syslog/journal.
You can even map other keys to nccm keys - for example
instead of F1 you want to use F12 - just put the code for
F12 in the F1 key position.


Controls
--------

In nccm_config_controlmode == std mode:

- Up/Down arrows:     Move the marker the traditional way
- Home/End:           Jump marker to list first/last entry
- PgUp/PgDn:          Page up/down in the list

In nccm_config_controlmode == focus mode:

- Up/Down arrows:     Scroll the list up/down
- Home/End:           Jump to list first/last entry
- PgUp/PgDn:          Page up/down in the list
- Shift Up/Down:      Move the marker up/down
- Shift Left/Right:   Move the marker to display top/bottom

In both modes:

- Left/Right arrows:  Scroll the list horizontally
- Tab:                Switch between text boxes
- Enter or Ctrl-m:    Connect to the selected entry
- Ctrl-h:             Display this help menu
- Ctrl-k:             Toggle cursor mode std <--> focus
- Ctrl-q or
- Ctrl-c or
- Ctrl-d:             Quit the program
- F1-F5 or !@#$% :    Sort by respective column (1-5)


Usage
-----

`Conn` textbox:
Accepts integer values only (and:  `!@#$%`  for sorting).
Pressing Enter here will connect to this connection ID,
as corresponding to a valid value in the full
unfiltered list (even if that particular connection
is hidden by unmatching text in the `Filter` textbox),
ignoring everything else (Filter textbox, highlighted
line) - even if they don't match.
If this textbox is empty, it will connect to the
connection marked by the highlighted line.

`Filter` textbox:
Type any filter text here.
Filtering occurs by searching text present in all visible
columns (does not search in any of the non-visble
settings you made in nccm.yml for example identity or
customargs).
Accepts any printable character and space.
Text is forced to lowercase, and the resulting filtering
is case insensitive.
Pressing Enter will connect to the connection highlighed
in red. This also works if you're in the `Conn` textbox
and it's empty.
In cycle mode  `( nccm_loop_nccm == true )` - the value
of this field is stored for the next cycle.

Textboxes accept backspace to delete one char backwards,
inline editing not supported.

Displayed connection list is filtered by the combined
contents of all the fields as you type in real time.
Spaces delimit filters if typed into `Filter` textbox
and all filter entries are AND'ed.

nccm_config_controlmode == focus was inspired by vim
where you can move your display up/down around your work
while keeping your current line selected.


Command line arguments
----------------------

* Supply initial filtering text. These are considered part
    of the Filter field and are AND'ed. Examples:
      `nccm abc xyz`
      `nccm -d ab cd ef`
    If there is only one match - nccm will connect to it
    immediately.
    In cycle mode  `( nccm_loop_nccm == true )` - these args
    are stored in the  `Filter`  textbox for the next cycle.

* -h  or --help :
    Display the help message.

* -d  or --debug :
    Force debug verbosity logging, ignoring any other
    logging settings everywhere else.

* --logprivateinfo :
    Force nccm to expose private information in syslog
    (secure by default - logs `CENSORED` instead).

* -m  or --man :
    Display the man page.

* -v or --version :
    Display nccm version.


Sorting
-------

`F1-F5` keys sort by the respective fields 1-5.
The display shows 4 visible columms but we treat
username and server address as separate columns for
sorting purposes.
The Fn keys may be captured by certain GUIs or some
terminals send the Fn keys using different codes -
so we have an alternative - when focused on `Conn`
window, press Shift-1 through 5 (`!@#$%`) to toggle
sorting by the respective field number. Pressing the same
key again reverses the sort order. If you type these special
characters in the `Filter` textbox they become standard
filters just like any printable character.

```
Column #  Column name       Sort    Alternate sort
--------  -----------       ----    --------------
1         List serial #     F1      !
2         Friendly name     F2      @
3         User name         F3      #
4         Server address    F4      $
5         Comment           F5      %
```


Help text
---------

From within nccm: use `Ctrl-h` to display the help text.
From the command line: use `nccm -h` or `nccm --help`.
There isn't a man page yet so `man nccm` won't work.


Limitations
-----------

Will not store passwords. Please don't request this
feature because it won't be added.
Either use ssh passwordless login (by placing your
public key on the server in `.ssh/authorized_keys` - tip:
look up `ssh-copy-id`) or store your password in a
password manager and paste it when prompted.

Does not like window resizing and exits gracefully
displaying an error message.
It's safe to resize the window once connection
establishment is in progress or after connected to
your server.

Does not support highlighting filter keywords in search
results because this results in a messy and confusing
display once more than a couple keywords are used.
This is not even required because you can use filtering
to narrow down the search results to what you need.

Text entry is limited to the length of the textboxes
which in turn are dictated by the width of your window.
This should be enough for most use cases though.


Troubleshooting
---------------

Starting nccm:

The most common problem for existing installations is
user errors in the nccm.yml file.
Try `yamllint nccm.yml`. If yamllint passes and
nccm still fails: run as `nccm -d` and check syslog for
errors - you may see a message about the connection item
line that fails or at least the last line that succeeded.

The most common problem for new installations is
missing Python3 dependencies.
Run nccm and read the exception message - it will tell
you what's missing.

The second most common problem is different nccm and
nccm.yml versions. This usually happens if you download
a newer nccm version and use your existing and older
nccm.yml file although the reverse is true too. The error
will normally be in the `Load` method and the resulting
exception will resemble something like this (the line
number will be different):
`File "/usr/local/bin/nccm", line 481, in Load`.
If this happens, best is to backup your nccm.yml then
download both nccm and nccm.yml, verify that nccm now
works properly, then update the newly downloaded nccm.yml
from your backup copy.

Logging:
Look at your syslog file for nccm entries. Depending upon
the verbosity level set in the config file you may not see
much if at all anything.
By default the production level of the script logs INFO
and above which is not much.
Different syslog implementations have their own tolerance
for line length, and to handle all scenarios - very long
log lines are split into multiple lines, with wrapped
lines being marked with:
`    ....!!LINEWRAPPED!!`.

Increase logging verbosity level to `debug` using the
`-d` or `--debug` command line arguments.
This is by far the easiest way to debug and covers most
scenarios except for faults that occur before the code
actually reads the `-d` command line argument.

To permanently increase logging verbosity change this line
in the `nccm.yml` config file to debug:
`nccm_config_loglevel: debug`
This only comes into effect after the config file has
successfully loaded (does not change the log level for
code that runs before loading the config file).

And to log stuff that happens before the config file is
loaded and before the argument parser sets the debug level,
change this line inside the nccm code:
`LogLevel = logging.DEBUG`
Extra logging controls can be found in the code under the
`Variables that control logging` section.

Also - more debugging calls exist but are commented out in
the code due to too much logging. Enable them as required.

To completely disable logging - uncomment this line:
`logging.disable(level=logging.CRITICAL)`  .

By default nccm protects your privacy and security by
replacing items such as username and hostname with
`CENSORED` in syslog/journal. Supply the argument
`--logprivateinfo` if you wish to expose private
information to these logs.
You can also enable this permanently via the nccm.yml
config file (disabled by default).
Warning - any user who has access to the log files will
be able to see this information.
When this is enabled you will see:  `LogPrv` in red in the
help line at the bottom of the screen.

When you use ssh (either directly from the shell or wrapped
by nccm) - ssh always exits with an exit code. Exit code 0
means normal exit and non zero for other scenarios.
If you're getting messages from nccm saying ssh exited
non-zero - try running ssh directly from the shell and
immediately after it exits type `echo $?` - this will
display the error code. Remember - nccm doesn't cause ssh
to exit non-zero, all it does is expose this fact to the
user.

If you find bugs please update to the latest version of
nccm first (this may include updating your yaml file in
case the format changed). If the bug persists please report
it through the `issues` tab in github.


Hacking nccm
------------

Take something good and make it better!
The code is heavily commented, with the hope that it will
make life easier for modders and forkers.

The config file is simple yaml. If you already have a
collection of logins elsewhere in an accessible format -
writing a script to convert and append fields to nccm.yml
is easy.


Misc
----

This program aims to do one thing well - lets you make SSH
connections from an ncurses based manager with minimum
distraction. Feature requests that keep nccm on focus will
be considered.


Credits
-------

Big thanks goes to Andrew P. for suggesting features and
submitting improvements.

