#!/usr/bin/env python
"""
================================================================================
:mod:`config_gui` -- PENEPMA Monte Carlo program GUI configuration
================================================================================

.. module:: config_gui
   :synopsis: PENEPMA Monte Carlo program GUI configuration

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
from PySide.QtGui import QSpinBox, QSizePolicy

# Local modules.
from pymontecarlo.program.config_gui import GUI, _ConfigurePanelWidget
from pymontecarlo.program.penepma.config import program

from pymontecarlo.ui.gui.util.widget import FileBrowseWidget, DirBrowseWidget

# Globals and constants variables.

class _PenepmaConfigurePanelWidget(_ConfigurePanelWidget):

    def _initUI(self, settings):
        # Widgets
        self._brw_pendbase = DirBrowseWidget()

        self._brw_exe = FileBrowseWidget()
        if os.name == 'nt':
            self._brw_exe.setNameFilter('Application files (*.exe)')
        else:
            self._brw_exe.setNameFilter('Application files (*)')

        self._spn_dumpp = QSpinBox()
        self._spn_dumpp.setMinimum(30)
        self._spn_dumpp.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Layouts
        layout = _ConfigurePanelWidget._initUI(self, settings)
        layout.addRow("Path to pendbase directory", self._brw_pendbase)
        layout.addRow('Path to PENEPMA executable', self._brw_exe)
        layout.addRow('Interval between dump (s)', self._spn_dumpp)

        # Signals
        self._brw_pendbase.pathChanged.connect(self._onPathChanged)
        self._brw_exe.pathChanged.connect(self._onPathChanged)

        # Values
        if 'penepma' in settings:
            path = getattr(settings.penepma, 'pendbase', None)
            try:
                self._brw_pendbase.setPath(path)
            except ValueError:
                pass

            path = getattr(settings.penepma, 'exe', None)
            try:
                self._brw_exe.setPath(path)
            except ValueError:
                pass

            try:
                dumpp = int(getattr(settings.penepma, 'dumpp', 30))
                self._spn_dumpp.setValue(dumpp)
            except (TypeError, ValueError):
                pass

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

    def updateSettings(self, settings):
        section = _ConfigurePanelWidget.updateSettings(self, settings)
        section.pendbase = self._brw_pendbase.path()
        section.exe = self._brw_exe.path()
        section.dumpp = int(self._spn_dumpp.value())
        return section

class _PenepmaGUI(GUI):

    def create_configure_panel(self, parent=None):
        """
        Returns the configure panel for this program.

        :arg parent: parent window
        :arg settings: settings object
        """
        return _PenepmaConfigurePanelWidget(program, parent)

gui = _PenepmaGUI()
