#!/usr/bin/env python
"""
================================================================================
:mod:`config_gui` -- PENSHOWER Monte Carlo program GUI configuration
================================================================================

.. module:: config_gui
   :synopsis: PENSHOWER Monte Carlo program GUI configuration

"""

# Script information for the file.
__author__ = "Philippe T. Pinard"
__email__ = "philippe.pinard@gmail.com"
__version__ = "0.1"
__copyright__ = "Copyright (c) 2012 Philippe T. Pinard"
__license__ = "GPL v3"

# Standard library modules.
import os

# Third party modules.

# Local modules.
from pymontecarlo.program.config_gui import GUI, _ConfigurePanelWidget
from pymontecarlo.program.penshower.config import program

from pymontecarlo.ui.gui.util.widget import FileBrowseWidget, DirBrowseWidget

# Globals and constants variables.

class _PenshowerConfigurePanelWidget(_ConfigurePanelWidget):

    def _initUI(self):
        # Widgets
        self._brw_pendbase = DirBrowseWidget()

        self._brw_exe = FileBrowseWidget()
        if os.name == 'nt':
            self._brw_exe.setNameFilter('Application files (*.exe)')
        else:
            self._brw_exe.setNameFilter('Application files (*)')

        # Layouts
        layout = _ConfigurePanelWidget._initUI(self)
        layout.addRow("Path to pendbase directory", self._brw_pendbase)
        layout.addRow('Path to PENSHOWER executable', self._brw_exe)

        # Signals
        self._brw_pendbase.pathChanged.connect(self._onPathChanged)
        self._brw_exe.pathChanged.connect(self._onPathChanged)

        return layout

    def _onPathChanged(self, path):
        if not path:
            return
        if not self._brw_pendbase.baseDir():
            self._brw_pendbase.setBaseDir(path)
        if not self._brw_exe.baseDir():
            self._brw_exe.setBaseDir(path)

    def hasAcceptableInput(self):
        if not self._brw_pendbase.path():
            return False
        if not self._brw_exe.path():
            return False
        if not os.access(self._brw_exe.path(), os.X_OK):
            return False
        return True

    def setSettings(self, settings):
        if 'penshower' in settings:
            path = getattr(settings.penshower, 'pendbase', None)
            try:
                self._brw_pendbase.setPath(path)
            except ValueError:
                pass

            path = getattr(settings.penshower, 'exe', None)
            try:
                self._brw_exe.setPath(path)
            except ValueError:
                pass

    def updateSettings(self, settings):
        section = _ConfigurePanelWidget.updateSettings(self, settings)
        section.pendbase = self._brw_pendbase.path()
        section.exe = self._brw_exe.path()
        return section

class _PenshowerGUI(GUI):

    def create_configure_panel(self, parent=None):
        """
        Returns the configure panel for this program.

        :arg parent: parent window
        :arg settings: settings object
        """
        return _PenshowerConfigurePanelWidget(program, parent)

gui = _PenshowerGUI()
