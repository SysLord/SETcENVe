
'''
Copyright 2012 Christian Helmer

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.


Author: Christian Helmer
Date: 27.12.2010

--------------------------------------------------------------------------------

SETcENVe = SEmigraphical Tool for Comfortable ENvironment Variable Editing
To eliminate the need of 20 clicks just to change an environment variable.

Currently only handles the PATH variable.

FOR WINDOWS ONLY
Tested on Windows 7 64Bit

Info:
Should be self-explanatory.
To simplify appending, enable QuickEdit for all consoles: rightclick = paste

To copy entries between user- and system-path there is a buffer.
This buffer works like a stack.
With c<nr> an entry is pushed on top of the stack.
p appends the entry to current list.

c5 copies entry 5 to buffer
d2 deletes entry 2

Changes are only saved when [w]rite is used explicitly.

The environment and path data is stored in the Registry and it seems,
that updates can only be pushed to applications with a message broadcast.
Windows cmd is not updated while running because it is somehow special.
'''

import sys
import win32api, win32con, win32gui

def shorten(txt, soft, hard):
  if len(txt) > hard:
    return txt[:soft-4] + "..."
  return txt

''' get environment variable '''
def getenv(userOrSystem, varname):
  v = ""
  try:
    if userOrSystem == "system":
      rkey = win32api.RegOpenKey(win32con.HKEY_LOCAL_MACHINE,
      'SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment')

    elif userOrSystem == "user":
      rkey = win32api.RegOpenKey(win32con.HKEY_CURRENT_USER, 'Environment')

    else:
      raise Exception('wrong parameter')


    if varname == "":
      # list entries
      keycount = win32api.RegQueryInfoKey(rkey)[1]
      
      pairs = {}
      for keyidx in range(keycount):
        name,value,_ = win32api.RegEnumValue(rkey, keyidx)
        pairs[name] = value
      return pairs
    else:
      try:
        v = str(win32api.RegQueryValueEx(rkey, varname)[0])
        # dangerous because we overwrite variables with expanded values
        #v = win32api.ExpandEnvironmentStrings(v)
      except:
        # TODO
        # pass, because it might not exist
        pass
  finally:
    win32api.RegCloseKey(rkey)
  return v


''' set environment variable '''
def setenv(userOrSystem, varname, val):
  try:
    if userOrSystem == "system":
      rkey = win32api.RegOpenKey(win32con.HKEY_LOCAL_MACHINE,
      'SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment', 0,
      win32con.KEY_SET_VALUE)
    elif userOrSystem == "user":
      rkey = win32api.RegOpenKey(win32con.HKEY_CURRENT_USER,
      'Environment', 0,
      win32con.KEY_SET_VALUE)
    else:
      raise Exception('wrong parameter')
      
    try:
      win32api.RegSetValueEx(rkey, varname, 0, win32con.REG_SZ, val)
    except:
      raise
  finally:
    win32api.RegCloseKey(rkey)

''' broadcast the change of environment variables '''
def broadcastChanges():

  try:
    # send message to all windows: environment vars have changed
    rc, dwReturnValue = win32gui.SendMessageTimeout(
        win32con.HWND_BROADCAST,
        win32con.WM_SETTINGCHANGE,
        0,
        "Environment",
        win32con.SMTO_ABORTIFHUNG,
        5000)
  except:
    # ignore errors
    pass
    
def main():
  # colorama? for easy console colors
  try:
    import colorama
    colorama.init()
    caRed = colorama.Fore.RED
    caGreen = colorama.Fore.GREEN
    caReset = colorama.Fore.RESET
  except:
    caRed = ""
    caGreen = ""
    caReset = ""

  userOrSystem = "user"
  curValue = "PATH"
  refresh = True

  # buffer stack
  buf = []

  while(True):
    if refresh == True:
      refresh = False
      readpath = getenv(userOrSystem, curValue)
      parts = readpath.split(";")

    print "--------------------------------------------------------------------------------"
    c = 0
    for p in parts:
      print str(c).zfill(2) + " " + shorten(p, 80, 120)
      c += 1

    print " "
    if len(buf) > 0:
      print "        Buffer:"
      first = "->"
      for b in reversed(buf):
        print "     " + first + " " + b
        first = "  "
    print " "
    print "([u]ser environment, [s]ystem environment)"
    print "([c]opy to buffer<nr>, [p]aste from buffer, p[o]p)"
    cmd  = raw_input("[r]ead, [w]rite, [a]ppend, [d]elete<nr>, [q]uit without saving: ")

    # evaluate user input
    
    # system or user variables?
    if cmd == "u":
      userOrSystem = "user"
      refresh = True
    elif cmd == "s":
      userOrSystem = "system"
      refresh = True

    # buffer copy and paste
    elif cmd.startswith("c"):
      try:
        cmd2 = cmd[1:]
        buf.append(parts[int(cmd2)])
      except:
        print caRed + "Did not work." + caReset

    elif cmd == "p":
      try:
        parts.append(buf.pop())
      except:
        print caRed + "Did not work." + caReset
    elif cmd == "o":
      try:
        buf.pop()
      except:
        print caRed + "Did not work." + caReset

    # read from registry
    elif cmd == "r":
      refresh = True

    # write and broadcast
    elif cmd == "w":
      newpath = ";".join(parts)
      print "writing..."
      setenv(userOrSystem, curValue, newpath)
      print "broadcasting..."
      broadcastChanges()
      print caGreen + "done" + caReset
      refresh = True

    # append and delete
    elif cmd == "a":
      app  = raw_input("append: ")
      parts.append(app)

    elif cmd.startswith("d"):
      try:
        cmd2 = cmd[1:]
        parts.pop(int(cmd2))
      except:
        print caRed + "Did not work." + caReset

    # quit
    elif cmd == "q":
      break
    else:
      print caRed + "I do not know this command: " + cmd + caReset


if __name__ == "__main__":
  sys.exit(main())


