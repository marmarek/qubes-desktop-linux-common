#!/usr/bin/python2
# coding=utf-8
#
# The Qubes OS Project, http://www.qubes-os.org
#
# Copyright (C) 2016  Marek Marczykowski-Górecki
#                               <marmarek@invisiblethingslab.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.

import colorsys
import os
import tempfile

import unittest
import pkg_resources
import qubesappmenus
import qubesappmenus.receive
import qubesimgconverter

class Label(object):
    def __init__(self, index, color, name):
        self.index = index
        self.color = color
        self.name = name

class TestApp(object):
    labels = {1: Label(1, '0xcc0000', 'red')}

    def __init__(self):
        self.domains = {}


class TestVM(object):
    # pylint: disable=too-few-public-methods
    app = TestApp()

    def __init__(self, name, **kwargs):
        self.running = False
        self.is_template = False
        self.name = name
        for k, v in kwargs.items():
            setattr(self, k, v)

    def is_running(self):
        return self.running

VMPREFIX = 'test-'

class TC_00_Appmenus(unittest.TestCase):
    """Unittests for appmenus, theoretically runnable from git checkout"""
    def setUp(self):
        super(TC_00_Appmenus, self).setUp()
        vmname = VMPREFIX + 'standalone'
        self.standalone = TestVM(
            name=vmname,
            updateable=True,
        )
        vmname = VMPREFIX + 'template'
        self.template = TestVM(
            name=vmname,
            updateable=True,
        )
        vmname = VMPREFIX + 'vm'
        self.appvm = TestVM(
            name=vmname,
            template=self.template,
            updateable=False,
        )
        self.app = TestApp()
        self.ext = qubesappmenus.Appmenus()
        self.basedir = os.path.expanduser('~/.local/share/qubes-appmenus')

    def test_000_templates_dir(self):
        self.assertEqual(
            self.ext.templates_dir(self.standalone),
            os.path.join(self.basedir,
                self.standalone.name, 'apps.templates')
        )
        self.assertEqual(
            self.ext.templates_dir(self.template),
            os.path.join(self.basedir,
                self.template.name, 'apps.templates')
        )
        self.assertEqual(
            self.ext.templates_dir(self.appvm),
            os.path.join(self.basedir,
                self.template.name, 'apps.templates')
        )

    def test_001_template_icons_dir(self):
        self.assertEqual(
            self.ext.template_icons_dir(self.standalone),
            os.path.join(self.basedir,
                self.standalone.name, 'apps.tempicons')
        )
        self.assertEqual(
            self.ext.template_icons_dir(self.template),
            os.path.join(self.basedir,
                self.template.name, 'apps.tempicons')
        )
        self.assertEqual(
            self.ext.template_icons_dir(self.appvm),
            os.path.join(self.basedir,
                self.template.name, 'apps.tempicons')
        )

    def test_002_appmenus_dir(self):
        self.assertEqual(
            self.ext.appmenus_dir(self.standalone),
            os.path.join(self.basedir,
                self.standalone.name, 'apps')
        )
        self.assertEqual(
            self.ext.appmenus_dir(self.template),
            os.path.join(self.basedir,
                self.template.name, 'apps')
        )
        self.assertEqual(
            self.ext.appmenus_dir(self.appvm),
            os.path.join(self.basedir,
                self.appvm.name, 'apps')
        )

    def test_003_icons_dir(self):
        self.assertEqual(
            self.ext.icons_dir(self.standalone),
            os.path.join(self.basedir,
                self.standalone.name, 'apps.icons')
        )
        self.assertEqual(
            self.ext.icons_dir(self.template),
            os.path.join(self.basedir,
                self.template.name, 'apps.icons')
        )
        self.assertEqual(
            self.ext.icons_dir(self.appvm),
            os.path.join(self.basedir,
                self.appvm.name, 'apps.icons')
        )

    def test_100_get_appmenus(self):
        self.maxDiff = None
        def _run(service, **kwargs):
            class PopenMockup(object):
                pass
            self.assertEqual(service, 'qubes.GetAppmenus')
            p = PopenMockup()
            p.stdout = pkg_resources.resource_stream(__name__,
                'test-data/appmenus.input')
            p.wait = lambda: None
            p.returncode = 0
            return p
        vm = TestVM('test-vm', run_service=_run)
        appmenus = qubesappmenus.receive.get_appmenus(vm)
        expected_appmenus = {
            'org.gnome.Nautilus': {
                'Name': 'Files',
                'Comment': 'Access and organize files',
                'Categories': 'GNOME;GTK;Utility;Core;FileManager;',
                'Exec': 'qubes-desktop-run '
                        '/usr/share/applications/org.gnome.Nautilus.desktop',
                'Icon': 'system-file-manager',
            },
            'org.gnome.Weather.Application': {
                'Name': 'Weather',
                'Comment': 'Show weather conditions and forecast',
                'Categories': 'GNOME;GTK;Utility;Core;',
                'Exec': 'qubes-desktop-run '
                        '/usr/share/applications/org.gnome.Weather.Application.desktop',
                'Icon': 'org.gnome.Weather.Application',
            },
            'org.gnome.Cheese': {
                'Name': 'Cheese',
                'GenericName': 'Webcam Booth',
                'Comment': 'Take photos and videos with your webcam, with fun graphical effects',
                'Categories': 'GNOME;AudioVideo;Video;Recorder;',
                'Exec': 'qubes-desktop-run '
                        '/usr/share/applications/org.gnome.Cheese.desktop',
                'Icon': 'cheese',
            },
            'evince': {
                'Name': 'Document Viewer',
                'Comment': 'View multi-page documents',
                'Categories': 'GNOME;GTK;Office;Viewer;Graphics;2DGraphics;VectorGraphics;',
                'Exec': 'qubes-desktop-run '
                        '/usr/share/applications/evince.desktop',
                'Icon': 'evince',
            },
        }
        self.assertEqual(expected_appmenus, appmenus)

    def test_110_create_template(self):
        values = {
            'Name': 'Document Viewer',
            'Comment': 'View multi-page documents',
            'Categories': 'GNOME;GTK;Office;Viewer;Graphics;2DGraphics;VectorGraphics;',
            'Exec': 'qubes-desktop-run '
                    '/usr/share/applications/evince.desktop',
            'Icon': 'evince',
        }
        expected_template = (
            '[Desktop Entry]\n'
            'Version=1.0\n'
            'Type=Application\n'
            'Terminal=false\n'
            'X-Qubes-VmName=%VMNAME%\n'
            'Icon=%VMDIR%/apps.icons/evince.png\n'
            'Name=%VMNAME%: Document Viewer\n'
            'Comment=View multi-page documents\n'
            'Categories=GNOME;GTK;Office;Viewer;Graphics;2DGraphics'
            ';VectorGraphics;X-Qubes-VM;\n'
            'Exec=qvm-run -q -a --service -- %VMNAME% qubes.StartApp+evince\n'
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'evince.desktop')
            qubesappmenus.receive.create_template(
                path, 'evince', values, False)
            with open(path) as f:
                actual_template = f.read()
            self.assertEqual(actual_template, expected_template)

    def test_111_create_template_legacy(self):
        values = {
            'Name': 'Document Viewer',
            'Comment': 'View multi-page documents',
            'Categories': 'GNOME;GTK;Office;Viewer;Graphics;2DGraphics;VectorGraphics;',
            'Exec': 'qubes-desktop-run '
                    '/usr/share/applications/evince.desktop',
            'Icon': 'evince',
        }
        expected_template = (
            '[Desktop Entry]\n'
            'Version=1.0\n'
            'Type=Application\n'
            'Terminal=false\n'
            'X-Qubes-VmName=%VMNAME%\n'
            'Icon=%VMDIR%/apps.icons/evince.png\n'
            'Name=%VMNAME%: Document Viewer\n'
            'Comment=View multi-page documents\n'
            'Categories=GNOME;GTK;Office;Viewer;Graphics;2DGraphics'
            ';VectorGraphics;X-Qubes-VM;\n'
            'Exec=qvm-run -q -a %VMNAME% -- \'qubes-desktop-run '
            '/usr/share/applications/evince.desktop\'\n'
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'evince.desktop')
            qubesappmenus.receive.create_template(
                path, 'evince', values, True)
            with open(path) as f:
                actual_template = f.read()
            self.assertEqual(actual_template, expected_template)


def list_tests():
    return (TC_00_Appmenus,)
