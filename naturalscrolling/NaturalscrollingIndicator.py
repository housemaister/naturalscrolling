#!/usr/bin/env python
import sys
import os
import gtk
import appindicator

from naturalscrolling_lib import naturalscrollingconfig
from naturalscrolling_lib import SwissKnife
from naturalscrolling_lib.GConfSettings import *
from naturalscrolling.AboutNaturalscrollingDialog import AboutNaturalscrollingDialog

import gettext
from gettext import gettext as _
gettext.textdomain('naturalscrolling')

class NaturalscrollingIndicator:
    
    def __init__(self):
        self.AboutDialog = AboutNaturalscrollingDialog
        self.mouseids = self.get_slave_pointers()
        self.pingfrequency = 1 # in seconds
        
        self.ind = appindicator.Indicator(
            "natural-scrolling-indicator",
            "natural-scrolling-status-not-activated",
            appindicator.CATEGORY_APPLICATION_STATUS
        )
        self.settings = GConfSettings()

        media_path = "%s/media/" % naturalscrollingconfig.get_data_path()
        self.ind.set_icon_theme_path(media_path)
        self.ind.set_attention_icon("natural-scrolling-status-activated")
        
        self.menu_setup()
        self.ind.set_menu(self.menu)

    def get_slave_pointers(self):
        xinput_reader = SwissKnife.XinputReader()
        xinput = SwissKnife.Xinput()

        return xinput_reader.get_slave_pointer(xinput.list())

    def menu_setup(self):
        self.menu = gtk.Menu()
        
        #natural scrolling
        self.menu_item_natural_scrolling = gtk.CheckMenuItem(_('Natural Scrolling'))
        self.enable_natural_scrolling(
            self.settings.key(GCONF_NATURAL_SCROLLING_KEY).is_enable()
        )
        self.menu_item_natural_scrolling.connect('activate', self.on_natural_scrolling_toggled)
        self.settings.server().fire_me_when_update_on_key(GCONF_NATURAL_SCROLLING_KEY, self.enable_natural_scrolling)
        self.menu_item_natural_scrolling.show()

        #seperator 1
        self.menu_item_seperator1 = gtk.SeparatorMenuItem()
        self.menu_item_seperator1.show()

        #preferences
        self.menu_sub = gtk.Menu()

        self.menu_item_preferences = gtk.MenuItem(_('Preferences'))
        self.menu_item_start_at_login = gtk.CheckMenuItem(_('Start at login'))
        if os.path.isfile(naturalscrollingconfig.get_auto_start_file_path()):
            self.menu_item_start_at_login.set_active(True)
        self.menu_item_start_at_login.connect("activate", self.on_start_at_login_clicked)
        self.menu_sub.append(self.menu_item_start_at_login)
        self.menu_item_preferences.set_submenu(self.menu_sub)

        self.menu_item_start_at_login.show()
        self.menu_item_preferences.show()

        #about
        self.menu_item_about = gtk.MenuItem(_('About...'))
        self.menu_item_about.connect('activate', self.on_about_clicked)
        self.menu_item_about.show()

        #seperator 2
        self.menu_item_seperator2 = gtk.SeparatorMenuItem()
        self.menu_item_seperator2.show()

        #quit
        self.menu_item_quit = gtk.MenuItem(_('Quit Natural Scrolling'))
        self.menu_item_quit.connect("activate", self.quit)
        self.menu_item_quit.show()

        #add items to menu
        self.menu.append(self.menu_item_natural_scrolling)
        self.menu.append(self.menu_item_seperator1)
        self.menu.append(self.menu_item_preferences)
        self.menu.append(self.menu_item_about)
        self.menu.append(self.menu_item_seperator2)
        self.menu.append(self.menu_item_quit)

    def enable_natural_scrolling(self, enabled):
        """
        Global method to apply or not Natural Scrolling
        """
        for mouseid in self.mouseids:
            buttonmap = os.popen('xinput get-button-map %s' % mouseid).read().strip()
            
            if enabled == True:
                buttonmap = buttonmap.replace('4 5', '5 4')
                buttonmap = buttonmap.replace('6 7', '7 6')
                self.settings.key(GCONF_NATURAL_SCROLLING_KEY).enable()
                self.ind.set_status(appindicator.STATUS_ATTENTION)
            else:
                buttonmap = buttonmap.replace('5 4', '4 5')
                buttonmap = buttonmap.replace('7 6', '6 7')
                self.settings.key(GCONF_NATURAL_SCROLLING_KEY).disable()
                self.ind.set_status(appindicator.STATUS_ACTIVE)
            
            self.menu_item_natural_scrolling.set_active(enabled)
            
            os.system('xinput set-button-map %s %s' %(mouseid, buttonmap))

    def on_natural_scrolling_toggled(self, widget, data=None):
        """
        Fired method when user click on gtk.CheckMenuItem 'Natural Scrolling'
        """
        self.enable_natural_scrolling(widget.get_active())

    def on_start_at_login_clicked(self, widget, data=None):
        """
        Fired method when user click on gtk.CheckMenuItem 'Start at login'
        """
        if not os.path.exists(naturalscrollingconfig.get_auto_start_path()):
            os.makedirs(naturalscrollingconfig.get_auto_start_path())
        
        auto_start_file_exists = os.path.isfile(naturalscrollingconfig.get_auto_start_file_path())
        if widget.get_active():
            if not auto_start_file_exists:
                source = open(naturalscrollingconfig.get_data_path() + "/" + naturalscrollingconfig.get_auto_start_file_name(), "r")
                destination = open(naturalscrollingconfig.get_auto_start_file_path(), "w")
                destination.write(source.read())
                destination.close() and source.close()
        else:
            if auto_start_file_exists:
                os.remove(naturalscrollingconfig.get_auto_start_file_path())

    def on_about_clicked(self, widget, data=None):
        about = self.AboutDialog() # pylint: disable=E1102
        response = about.run()
        about.destroy()


    def isreversed(self):
        inreverseorder = False

        for id in self.mouseids:
            map = os.popen('xinput get-button-map %s' % id).read().strip()

            if '5 4' in map:
                inreverseorder = True
                break

        return inreverseorder


    def check_scrolling(self):
        if self.isreversed():
            self.ind.set_status(appindicator.STATUS_ATTENTION)
        else:
            self.ind.set_status(appindicator.STATUS_ACTIVE)
       
        return True


    def main(self):
        self.check_scrolling()
        gtk.timeout_add(self.pingfrequency * 1000, self.check_scrolling)

        gtk.main()


    def quit(self, widget):
        sys.exit(0)

