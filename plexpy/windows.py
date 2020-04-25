# -*- coding: utf-8 -*-

# This file is part of Tautulli.
#
#  Tautulli is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Tautulli is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Tautulli.  If not, see <http://www.gnu.org/licenses/>.

import os
import shlex
import sys
from systray import SysTrayIcon
import winreg

import plexpy
if plexpy.PYTHON2:
    import common
    import logger
    import versioncheck
else:
    from plexpy import common
    from plexpy import logger
    from plexpy import versioncheck


class WindowsSystemTray(object):
    def __init__(self):
        self.image_dir = os.path.join(plexpy.PROG_DIR, 'data/interfaces/', plexpy.CONFIG.INTERFACE, 'images')

        if plexpy.UPDATE_AVAILABLE:
            self.icon = os.path.join(self.image_dir, 'logo-circle-update.ico')
            self.hover_text = common.PRODUCT + ' - Update Available!'
        else:
            self.icon = os.path.join(self.image_dir, 'logo-circle.ico')
            self.hover_text = common.PRODUCT

        if plexpy.CONFIG.LAUNCH_STARTUP:
            start_icon = os.path.join(self.image_dir, 'check-solid.ico')
        else:
            start_icon = None

        self.menu_options = [
            ['Open Tautulli', None, self.tray_open, 'default'],
            ['', None, 'separator', None],
            ['Start Tautulli at Login', start_icon, self.tray_startup, None],
            ['', None, 'separator', None],
            ['Check for Updates', None, self.tray_check_update, None],
            ['Update', None, self.tray_update, None],
            ['Restart', None, self.tray_restart, None]
        ]

        self.sys_tray_icon = None
        self.start()

    def start(self):
        logger.info("Launching system tray icon.")
        try:
            self.sys_tray_icon = SysTrayIcon(self.icon, self.hover_text, self.menu_options, on_quit=self.tray_quit)
            self.sys_tray_icon.start()
        except Exception as e:
            logger.error("Unable to launch system tray icon: %s." % e)

    def shutdown(self):
        self.sys_tray_icon.shutdown()

    def update(self, **kwargs):
        self.sys_tray_icon.update(**kwargs)

    def tray_open(self, sysTrayIcon):
        plexpy.launch_browser(plexpy.CONFIG.HTTP_HOST, plexpy.HTTP_PORT, plexpy.HTTP_ROOT)

    def tray_startup(self, sysTrayIcon):
        plexpy.CONFIG.LAUNCH_STARTUP = not plexpy.CONFIG.LAUNCH_STARTUP
        set_startup()

    def tray_check_update(self, sysTrayIcon):
        versioncheck.check_update()

    def tray_update(self, sysTrayIcon):
        if plexpy.UPDATE_AVAILABLE:
            plexpy.SIGNAL = 'update'
        else:
            hover_text = common.PRODUCT + ' - No Update Available'
            self.update(hover_text=hover_text)

    def tray_restart(self, sysTrayIcon):
        plexpy.SIGNAL = 'restart'

    def tray_quit(self, sysTrayIcon):
        plexpy.SIGNAL = 'shutdown'

    def change_tray_startup_icon(self):
        if plexpy.CONFIG.LAUNCH_STARTUP:
            start_icon = os.path.join(self.image_dir, 'check-solid.ico')
        else:
            start_icon = None
        self.menu_options[2][1] = start_icon
        self.update(menu_options=self.menu_options)


def set_startup():
    if plexpy.WIN_SYS_TRAY_ICON:
        plexpy.WIN_SYS_TRAY_ICON.change_tray_startup_icon()

    startup_reg_path = "Software\\Microsoft\\Windows\\CurrentVersion\\Run"

    exe = sys.executable
    if plexpy.FROZEN:
        args = [exe]
    else:
        args = [exe, plexpy.FULL_PATH]

    args += ['--nolaunch']

    cmd = ' '.join(shlex.quote(arg) for arg in args).replace('python.exe', 'pythonw.exe').replace("'", '"')

    if plexpy.CONFIG.LAUNCH_STARTUP:
        try:
            winreg.CreateKey(winreg.HKEY_CURRENT_USER, startup_reg_path)
            registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, startup_reg_path, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(registry_key, common.PRODUCT, 0, winreg.REG_SZ, cmd)
            winreg.CloseKey(registry_key)
            logger.info("Added Tautulli to Windows system startup registry key.")
            return True
        except WindowsError as e:
            logger.error("Failed to create Windows system startup registry key: %s", e)
            return False

    else:
        try:
            registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, startup_reg_path, 0, winreg.KEY_ALL_ACCESS)
            winreg.DeleteValue(registry_key, common.PRODUCT)
            winreg.CloseKey(registry_key)
            logger.info("Removed Tautulli from Windows system startup registry key.")
            return True
        except WindowsError as e:
            logger.error("Failed to delete Windows system startup registry key: %s", e)
            return False