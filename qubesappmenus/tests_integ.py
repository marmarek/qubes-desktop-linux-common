# -*- encoding: utf8 -*-
#
# The Qubes OS Project, http://www.qubes-os.org
#
# Copyright (C) 2017 Marek Marczykowski-Górecki
#                               <marmarek@invisiblethingslab.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, see <http://www.gnu.org/licenses/>.

import os
import xdg

import qubes
import qubes.tests
import qubes.tests.extra
import qubes.vm.templatevm
import qubes.vm.appvm

import qubesimgconverter
import colorsys
from functools import reduce
import qubesappmenus


class TC_10_AppmenusIntegration(qubes.tests.extra.ExtraTestCase):
    def setUp(self):
        super(TC_10_AppmenusIntegration, self).setUp()
        self.vm = self.create_vms(['vm'])[0]
        self.appmenus = qubesappmenus.Appmenus()

    def assertPathExists(self, path):
        if not os.path.exists(path):
            self.fail("Path {} does not exist".format(path))

    def assertPathNotExists(self, path):
        if os.path.exists(path):
            self.fail("Path {} exists while it should not".format(path))

    def get_whitelist(self, whitelist_path):
        self.assertPathExists(whitelist_path)
        with open(whitelist_path) as f:
            whitelisted = [x.rstrip() for x in f.readlines()]
        return whitelisted

    def test_000_created(self, vm=None):
        if vm is None:
            vm = self.vm
        whitelist_path = os.path.join(vm.dir_path,
            qubesappmenus.AppmenusSubdirs.whitelist)
        whitelisted = self.get_whitelist(whitelist_path)
        self.assertPathExists(self.appmenus.appmenus_dir(vm))
        appmenus = os.listdir(self.appmenus.appmenus_dir(vm))
        self.assertTrue(all(x.startswith(vm.name + '-') for x in appmenus))
        appmenus = [x[len(vm.name) + 1:] for x in appmenus]
        self.assertIn('vm.directory', appmenus)
        appmenus.remove('vm.directory')
        self.assertIn('qubes-appmenu-select.desktop', appmenus)
        appmenus.remove('qubes-appmenu-select.desktop')
        self.assertEquals(set(whitelisted), set(appmenus))
        self.assertPathExists(self.appmenus.icons_dir(vm))
        appicons = os.listdir(self.appmenus.icons_dir(vm))
        whitelisted_icons = set()
        for appmenu in whitelisted:
            desktop = xdg.DesktopEntry.DesktopEntry(
                os.path.join(self.appmenus.appmenus_dir(vm),
                    '-'.join((vm.name, appmenu))))
            if desktop.getIcon():
                whitelisted_icons.add(os.path.basename(desktop.getIcon()))
        self.assertEquals(set(whitelisted_icons), set(appicons))

    def test_001_created_registered(self):
        """Check whether appmenus was registered in desktop environment"""
        whitelist_path = os.path.join(self.vm.dir_path,
            qubesappmenus.AppmenusSubdirs.whitelist)
        if not os.path.exists(whitelist_path):
            self.skipTest("Appmenus whitelist does not exists")
        whitelisted = self.get_whitelist(whitelist_path)
        for appmenu in whitelisted:
            if appmenu.endswith('.directory'):
                subdir = 'desktop-directories'
            else:
                subdir = 'applications'
            self.assertPathExists(os.path.join(
                xdg.BaseDirectory.xdg_data_home, subdir,
                '-'.join([self.vm.name, appmenu])))
        # TODO: some KDE specific dir?

    def test_002_unregistered_after_remove(self):
        """Check whether appmenus was unregistered after VM removal"""
        whitelist_path = os.path.join(self.vm.dir_path,
            qubesappmenus.AppmenusSubdirs.whitelist)
        if not os.path.exists(whitelist_path):
            self.skipTest("Appmenus whitelist does not exists")
        whitelisted = self.get_whitelist(whitelist_path)
        self.vm.remove_from_disk()
        for appmenu in whitelisted:
            if appmenu.endswith('.directory'):
                subdir = 'desktop-directories'
            else:
                subdir = 'applications'
            self.assertPathNotExists(os.path.join(
                xdg.BaseDirectory.xdg_data_home, subdir,
                '-'.join([self.vm.name, appmenu])))

    def test_003_created_template_empty(self):
        tpl = self.app.add_new_vm(qubes.vm.templatevm.TemplateVM,
            name=self.make_vm_name('tpl'), label='red')
        tpl.create_on_disk()
        self.assertPathExists(self.appmenus.templates_dir(tpl))
        self.assertPathExists(self.appmenus.template_icons_dir(tpl))

    def test_004_created_template_from_other(self):
        tpl = self.app.add_new_vm(qubes.vm.templatevm.TemplateVM,
            name=self.make_vm_name('tpl'), label='red')
        tpl.clone_disk_files(self.app.default_template)
        self.assertPathExists(self.appmenus.templates_dir(tpl))
        self.assertPathExists(self.appmenus.template_icons_dir(tpl))
        self.assertPathExists(os.path.join(tpl.dir_path,
            qubesappmenus.AppmenusSubdirs.whitelist))

        for appmenu in os.listdir(self.appmenus.templates_dir(
                self.app.default_template)):
            self.assertPathExists(os.path.join(
                self.appmenus.templates_dir(tpl), appmenu))

        for appicon in os.listdir(self.appmenus.template_icons_dir(
                self.app.default_template)):
            self.assertPathExists(os.path.join(
                self.appmenus.template_icons_dir(tpl), appicon))

    def get_image_color(self, path, expected_color):
        """Return mean color of the image as (r, g, b) in float"""
        image = qubesimgconverter.Image.load_from_file(path)
        _, l, _ = colorsys.rgb_to_hls(
            *qubesimgconverter.hex_to_float(expected_color))

        def get_hls(pixels, l):
            for i in range(0, len(pixels), 4):
                r, g, b, a = tuple(ord(c) / 255. for c in pixels[i:i + 4])
                if a == 0.0:
                    continue
                h, _, s = colorsys.rgb_to_hls(r, g, b)
                yield h, l, s

        mean_hls = reduce(
            lambda x, y: (x[0] + y[0], x[1] + y[1], x[2] + y[2]),
            get_hls(image.data, l),
            (0, 0, 0)
        )
        mean_hls = map(lambda x: x / (mean_hls[1] / l), mean_hls)
        image_color = colorsys.hls_to_rgb(*mean_hls)
        return image_color

    def assertIconColor(self, path, expected_color):
        image_color_float = self.get_image_color(path, expected_color)
        expected_color_float = qubesimgconverter.hex_to_float(expected_color)
        if not all(map(lambda a, b: abs(a - b) <= 0.15,
                image_color_float, expected_color_float)):
            self.fail(
                "Icon {} is not colored as {}".format(path, expected_color))

    def test_010_icon_color(self, vm=None):
        if vm is None:
            vm = self.vm
        icons_dir = self.appmenus.icons_dir(vm)
        appicons = os.listdir(icons_dir)
        for icon in appicons:
            self.assertIconColor(os.path.join(icons_dir, icon),
                vm.label.color)

    def test_011_icon_color_label_change(self):
        """Regression test for #1606"""
        self.vm.label = 'green'
        self.test_010_icon_color()

    def test_020_clone(self):
        vm2 = self.app.add_new_vm(qubes.vm.appvm.AppVM,
            name=self.make_vm_name('vm2'), label='green')

        vm2.clone_properties(self.vm)
        vm2.clone_disk_files(self.vm)
        self.test_000_created(vm=vm2)
        self.test_010_icon_color(vm=vm2)


def list_tests():
    return (
        TC_10_AppmenusIntegration,
    )
