#!/usr/bin/python
# -*- coding: utf-8 -*
"""
Display notifications of your android device over KDEConnect.

Requires:
    pydbus
    kdeconnect
	gi.repository

@author Moritz Lüdecke
"""

import re
from pydbus import SessionBus
import argparse
import gi
gi.require_version('Notify', '0.7')
from gi.repository import Notify


SERVICE_BUS = 'org.kde.kdeconnect'
PATH = '/modules/kdeconnect'
DEVICE_PATH = PATH + '/devices'


class KDEConnectNotify():
    """
    """
    # available configuration parameters
    device_id = None

    debug = None
    terminal = None
    libnotify = None

    _bus = None
    _dev = None

    def __init__(self, use_terminal = True,
                 use_libnotify = True,
                 debug = False,
                 device_id = None,
                 device_name = None):
        """
        Get the device id
        """
        self.terminal = use_terminal
        self.libnotify = use_libnotify
        self.debug = debug

        if not self.terminal:
            self._debug('hide terminal messages')

        if not self.libnotify:
            self._debug('hide notifications')

        if use_libnotify:
            Notify.init('KDEConnect Notify')

        self._bus = SessionBus()

        if device_id is None:
            self.device_id = self._get_device_id(device_id, device_name)
            if self.device_id is None:
                self._debug('No device id found')
                return
        else:
            self.device_id = device_id

        self._debug('Device id is %s' % self.device_id)
        try:
            self._dev = self._bus.get(SERVICE_BUS,
                                      DEVICE_PATH + '/%s' % self.device_id)
        except Exception:
            self.device_id = None
            return

    def _get_device_id(self, device_id, device_name):
        """
        Find the device id
        """
        _dbus = self._bus.get(SERVICE_BUS, PATH)
        devices = _dbus.devices()

        if device_name is None and device_id is None and len(devices) == 1:
            return devices[0]

        self._debug('Search device name \'%s\'' % device_name)
        for id in devices:
            self._dev = self._bus.get(SERVICE_BUS, DEVICE_PATH + '/%s' % id)
            if device_name == self._dev.name:
                return id

        return None

    def _debug(self, text):
        if self.debug:
            print(text)

    def _print(self, text):
        if self.terminal:
            print(text)

    def _notify(self, summary, body, category = 'dialog-information'):
        if self.libnotify:
            notify = Notify.Notification.new(summary, body, category)
            notify.show()

    def _get_device(self):
        """
        Get the device
        """
        try:
            device = {
                'name': self._dev.name,
                'isReachable': self._dev.isReachable,
                'isTrusted': self._dev.isTrusted,
            }
        except Exception:
            return None

        return device

    def _get_notification_ids(self):
        """
        Get notification ids
        """
        try:
            return self._dev.activeNotifications()
        except Exception:
            return None

    def _get_notification(self, id):
        """
        Get the notification text
        """
        try:
            _path = DEVICE_PATH + '/' + self.device_id + '/notifications/' + id
            _notify = self._bus.get(SERVICE_BUS, _path)
            notification = {
                'app_name': _notify.appName,
                'text': _notify.ticker
            }
            return notification

        except Exception:
            return None

    def show_notifications(self):
        """
        TODO: Get the current metadatas
        """
        if self.device_id is None:
            self._print('No device found')
            self._notify('KDEConnect Notify', 'No device found')
            return False

        device = self._get_device()

        if device is None:
            summary = 'KDEConnect Notify'
        else:
            summary = device['name']

        if device is None or not device['isReachable'] or not device['isTrusted']:
            self._print('Device is disconnected')
            self._notify(summary, 'Device is disconnected')
            return False

        ids = self._get_notification_ids()
        size = len(ids)

        self._debug('%s notifications available' % size)
        self._print(summary + ':')
        if size == 0:
            self._print('  No notifications available')
            self._notify(summary, 'No notifications available')
            return True

        for id in ids:
            notif = self._get_notification(id)

            if notif is None:
                self._print('  Couldn\'t read any notification')
                self._notify(summary, 'Couldn\'t read any notification')
                return False

            prefix = id + ' ' if self.debug else ''
            self._print('  ' + prefix + notif['app_name'] + ': ' + notif['text'])
            sep = notif['text'].find('‐')
            title = notif['text'][:sep-1]
            text = notif['text'][sep+2:] + '\n<i>' + notif['app_name'] + '</i>'
            self._notify(title, text)

        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=
            'Display notifications of your android device over KDEConnect.')
    parser.add_argument('--debug', action='store_true',
                        help='print debug messages')
    parser.add_argument('-d', '--device-id',
                        help='set device id')
    parser.add_argument('-n', '--device-name',
                        help='set device name')
    parser.add_argument('--hide-notifications', action='store_true',
                        help='hide notifications')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='hide terminal messages')

    args = parser.parse_args()

    notify = KDEConnectNotify(not args.quiet,
                              not args.hide_notifications,
                              args.debug,
                              args.device_id,
                              args.device_name)
    result = notify.show_notifications()

    if not result:
        exit(1)
