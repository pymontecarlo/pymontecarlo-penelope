#!/usr/bin/env python
"""
================================================================================
:mod:`material` -- Material widgets
================================================================================

.. module:: material
   :synopsis: Material widgets

.. inheritance-diagram:: pymontecarlo.program._penelope.ui.gui.options.material

"""

# Script information for the file.
__author__ = "Philippe T. Pinard"
__email__ = "philippe.pinard@gmail.com"
__version__ = "0.1"
__copyright__ = "Copyright (c) 2014 Philippe T. Pinard"
__license__ = "GPL v3"

# Standard library modules.
from operator import methodcaller
from itertools import product

# Third party modules.
from PySide.QtGui import \
    (QVBoxLayout, QLabel, QTableView, QItemDelegate, QHeaderView, QToolBar,
     QAction, QMessageBox, QValidator, QWidget, QSizePolicy, QFormLayout,
     QHBoxLayout, QFrame, QGroupBox, QComboBox)
from PySide.QtCore import Qt, QAbstractTableModel, QModelIndex, QAbstractListModel

# Local modules.
from pymontecarlo.ui.gui.util.widget import \
    (MultiNumericalLineEdit, NumericalLineEdit, NumericalValidator,
     UnitComboBox)
from pymontecarlo.ui.gui.util.tango import getIcon

from pymontecarlo.ui.gui.options.material import MaterialDialog as _MaterialDialog

from pymontecarlo.program._penelope.options.material import Material, InteractionForcing

# Globals and constants variables.
from pymontecarlo.options.particle import PARTICLES, ELECTRON
from pymontecarlo.options.collision import COLLISIONS, DELTA

class _ElasticScatteringValidator(NumericalValidator):

    def validate(self, values):
        if len(values) == 0:
            return QValidator.Intermediate

        for value in values:
            if value < 0.0 or value > 0.2:
                return QValidator.Intermediate
        return QValidator.Acceptable

class _CutoffEnergyValidator(NumericalValidator):

    def validate(self, values):
        if len(values) == 0:
            return QValidator.Intermediate

        for value in values:
            if value < 0.0:
                return QValidator.Intermediate
        return QValidator.Acceptable

class _MaximumStepLengthValidator(NumericalValidator):

    def validate(self, values):
        if len(values) == 0:
            return QValidator.Intermediate

        for value in values:
            if value < 0.0:
                return QValidator.Intermediate
        return QValidator.Acceptable

class _InteractionForcingForcerValidator(NumericalValidator):

    def validate(self, value):
        if value == 0.0:
            return QValidator.Intermediate
        return QValidator.Acceptable

class _InteractionForcingWeightValidator(NumericalValidator):

    def validate(self, value):
        if value < 0.0 or value > 1.0:
            return QValidator.Intermediate
        return QValidator.Acceptable

class _ParticleItemModel(QAbstractListModel):

    def __init__(self):
        QAbstractListModel.__init__(self)
        self._particles = sorted(PARTICLES)

    def rowCount(self, *args, **kwargs):
        return len(self._particles)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or \
                not (0 <= index.row() < len(self._particles)):
            return None

        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter

        if role != Qt.DisplayRole:
            return None

        particle = self._particles[index.row()]
        return str(particle)

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        return Qt.ItemFlags(QAbstractTableModel.flags(self, index))

    def particle(self, index):
        return self._particles[index]

class _CollisionItemModel(QAbstractListModel):

    def __init__(self):
        QAbstractListModel.__init__(self)
        self._collisions = sorted(COLLISIONS)

    def rowCount(self, *args, **kwargs):
        return len(self._collisions)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or \
                not (0 <= index.row() < len(self._collisions)):
            return None

        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter

        if role != Qt.DisplayRole:
            return None

        collision = self._collisions[index.row()]
        return str(collision)

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        return Qt.ItemFlags(QAbstractTableModel.flags(self, index))

    def collision(self, index):
        return self._collisions[index]

class _InteractionForcingTableModel(QAbstractTableModel):

    def __init__(self):
        QAbstractTableModel.__init__(self)
        self._forcings = []

    def rowCount(self, *args, **kwargs):
        return len(self._forcings)

    def columnCount(self, *args, **kwargs):
        return 5

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or \
                not (0 <= index.row() < len(self._forcings)):
            return None

        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter

        if role == Qt.DisplayRole or role == Qt.ToolTipRole:
            particle, collision, forcer, weightlow, weighthigh = \
                self._forcings[index.row()]

            column = index.column()
            if column == 0:
                return str(particle)
            elif column == 1:
                return str(collision)
            elif column == 2:
                return str(forcer)
            elif column == 3:
                return str(weightlow)
            elif column == 4:
                return str(weighthigh)

        return None

    def headerData(self, section , orientation, role):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            if section == 0:
                return 'Particle'
            elif section == 1:
                return 'Collision'
            elif section == 2:
                return 'Forcer'
            elif section == 3:
                return 'Weight low'
            elif section == 4:
                return 'Weight high'
        elif orientation == Qt.Vertical:
            return str(section + 1)

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled

        return Qt.ItemFlags(QAbstractTableModel.flags(self, index) |
                            Qt.ItemIsEditable)

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid() or \
                not (0 <= index.row() < len(self._forcings)):
            return False

        row = index.row()
        column = index.column()
        self._forcings[row][column] = value

        self.dataChanged.emit(index, index)
        return True

    def insertRows(self, row, count=1, parent=None):
        if parent is None:
            parent = QModelIndex()
        self.beginInsertRows(QModelIndex(), row, row + count - 1)

        for _ in range(count):
            self._forcings.insert(row, [ELECTRON, DELTA, -1, 0.0, 1.0])

        self.endInsertRows()
        return True

    def removeRows(self, row, count=1, parent=None):
        if parent is None:
            parent = QModelIndex()
        self.beginRemoveRows(QModelIndex(), row, row + count - 1)

        for index in reversed(range(row, row + count)):
            self._forcings.pop(index)

        self.endRemoveRows()
        return True

    def interaction_forcings(self):
        forcings = {}
        for particle, collision, forcer, weightlow, weighthigh in self._forcings:
            forcing = InteractionForcing(particle, collision, forcer,
                                         (weightlow, weighthigh))
            forcings.setdefault((particle, collision), []).append(forcing)
        return list(product(*list(forcings.values())))

class _InteractionForcingDelegate(QItemDelegate):

    def __init__(self, parent=None):
        QItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        column = index.column()
        if column == 0:
            editor = QComboBox(parent)
            editor.setModel(_ParticleItemModel())
            return editor
        elif column == 1:
            editor = QComboBox(parent)
            editor.setModel(_CollisionItemModel())
            return editor
        elif column == 2:
            editor = NumericalLineEdit(parent)
            editor.setValidator(_InteractionForcingForcerValidator())
            return editor
        elif column == 3:
            editor = NumericalLineEdit(parent)
            editor.setValidator(_InteractionForcingWeightValidator())
            return editor
        elif column == 4:
            editor = NumericalLineEdit(parent)
            editor.setValidator(_InteractionForcingWeightValidator())
            return editor

    def setEditorData(self, editor, index):
        text = index.model().data(index, Qt.DisplayRole)
        column = index.column()
        if column == 0:
            editor.setCurrentIndex(editor.findText(text))
        elif column == 1:
            editor.setCurrentIndex(editor.findText(text))
        elif column == 2:
            editor.setText(text)
        elif column == 3:
            editor.setText(text)
        elif column == 4:
            editor.setText(text)

    def setModelData(self, editor, model, index):
        column = index.column()
        if column == 0:
            particle = editor.model().particle(editor.currentIndex())
            model.setData(index, particle)
        elif column == 1:
            collision = editor.model().collision(editor.currentIndex())
            model.setData(index, collision)
        elif column == 2:
            if not editor.hasAcceptableInput():
                return
            model.setData(index, editor.value())
        elif column == 3:
            if not editor.hasAcceptableInput():
                return
            model.setData(index, editor.value())
        elif column == 4:
            if not editor.hasAcceptableInput():
                return
            model.setData(index, editor.value())

class MaterialDialog(_MaterialDialog):

    def __init__(self, parent=None):
        _MaterialDialog.__init__(self, parent)
        self.setWindowTitle('Material')
        self.setMinimumWidth(1000)

    def _initUI(self):
        # Variables
        model_forcing = _InteractionForcingTableModel()

        # Actions
        act_add_forcing = QAction(getIcon("list-add"), "Add interaction forcing", self)
        act_remove_forcing = QAction(getIcon("list-remove"), "Remove interaction forcing", self)

        # Widgets
        self._lbl_elastic_scattering_c1 = QLabel('C1')
        self._lbl_elastic_scattering_c1.setStyleSheet("color: blue")
        self._txt_elastic_scattering_c1 = MultiNumericalLineEdit()
        self._txt_elastic_scattering_c1.setValidator(_ElasticScatteringValidator())
        self._txt_elastic_scattering_c1.setValues([0.0])

        self._lbl_elastic_scattering_c2 = QLabel('C2')
        self._lbl_elastic_scattering_c2.setStyleSheet("color: blue")
        self._txt_elastic_scattering_c2 = MultiNumericalLineEdit()
        self._txt_elastic_scattering_c2.setValidator(_ElasticScatteringValidator())
        self._txt_elastic_scattering_c2.setValues([0.0])

        self._lbl_cutoff_energy_inelastic = QLabel('Inelastic collisions')
        self._lbl_cutoff_energy_inelastic.setStyleSheet("color: blue")
        self._txt_cutoff_energy_inelastic = MultiNumericalLineEdit()
        self._txt_cutoff_energy_inelastic.setValidator(_CutoffEnergyValidator())
        self._txt_cutoff_energy_inelastic.setValues([50.0])
        self._cb_cutoff_energy_inelastic = UnitComboBox('eV')

        self._lbl_cutoff_energy_bremsstrahlung = QLabel('Bremsstrahlung emission')
        self._lbl_cutoff_energy_bremsstrahlung.setStyleSheet("color: blue")
        self._txt_cutoff_energy_bremsstrahlung = MultiNumericalLineEdit()
        self._txt_cutoff_energy_bremsstrahlung.setValidator(_CutoffEnergyValidator())
        self._txt_cutoff_energy_bremsstrahlung.setValues([50.0])
        self._cb_cutoff_energy_bremsstrahlung = UnitComboBox('eV')

        self._lbl_maximum_step_length = QLabel('Maximum step length')
        self._lbl_maximum_step_length.setStyleSheet("color: blue")
        self._txt_maximum_step_length = MultiNumericalLineEdit()
        self._txt_maximum_step_length.setValidator(_MaximumStepLengthValidator())
        self._txt_maximum_step_length.setValues([1e15])
        self._cb_maximum_step_length_unit = UnitComboBox('m')

        self._tbl_forcing = QTableView()
        self._tbl_forcing.setModel(model_forcing)
        self._tbl_forcing.setItemDelegate(_InteractionForcingDelegate())
        header = self._tbl_forcing.horizontalHeader()
        header.setResizeMode(QHeaderView.Stretch)

        self._tlb_forcing = QToolBar()
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._tlb_forcing.addWidget(spacer)
        self._tlb_forcing.addAction(act_add_forcing)
        self._tlb_forcing.addAction(act_remove_forcing)

        # Layouts
        layout = QHBoxLayout()

        layout.addLayout(_MaterialDialog._initUI(self), 1)

        frame = QFrame()
        frame.setFrameShape(QFrame.VLine)
        frame.setFrameShadow(QFrame.Sunken)
        layout.addWidget(frame)

        sublayout = QVBoxLayout()

        box_elastic_scattering = QGroupBox("Elastic scattering")
        boxlayout = QFormLayout()
        boxlayout.addRow(self._lbl_elastic_scattering_c1, self._txt_elastic_scattering_c1)
        boxlayout.addRow(self._lbl_elastic_scattering_c2, self._txt_elastic_scattering_c2)
        box_elastic_scattering.setLayout(boxlayout)
        sublayout.addWidget(box_elastic_scattering)

        box_cutoff_energy = QGroupBox("Cutoff energy")
        boxlayout = QFormLayout()
        boxsublayout = QHBoxLayout()
        boxsublayout.addWidget(self._txt_cutoff_energy_inelastic, 1)
        boxsublayout.addWidget(self._cb_cutoff_energy_inelastic)
        boxlayout.addRow(self._lbl_cutoff_energy_inelastic, boxsublayout)
        boxsublayout = QHBoxLayout()
        boxsublayout.addWidget(self._txt_cutoff_energy_bremsstrahlung, 1)
        boxsublayout.addWidget(self._cb_cutoff_energy_bremsstrahlung)
        boxlayout.addRow(self._lbl_cutoff_energy_bremsstrahlung, boxsublayout)
        box_cutoff_energy.setLayout(boxlayout)
        sublayout.addWidget(box_cutoff_energy)

        subsublayout = QFormLayout()
        subsubsublayout = QHBoxLayout()
        subsubsublayout.addWidget(self._txt_maximum_step_length, 1)
        subsubsublayout.addWidget(self._cb_maximum_step_length_unit)
        subsublayout.addRow(self._lbl_maximum_step_length, subsubsublayout)
        sublayout.addLayout(subsublayout)

        box_forcing = QGroupBox('Interaction forcing')
        boxlayout = QVBoxLayout()
        boxlayout.addWidget(self._tbl_forcing)
        boxlayout.addWidget(self._tlb_forcing)
        box_forcing.setLayout(boxlayout)
        sublayout.addWidget(box_forcing)

        sublayout.addStretch()

        layout.addLayout(sublayout, 1)

        # Signals
        self._txt_elastic_scattering_c1.textChanged.connect(self._onElasticScatteringC1Changed)
        self._txt_elastic_scattering_c2.textChanged.connect(self._onElasticScatteringC2Changed)
        self._txt_cutoff_energy_inelastic.textChanged.connect(self._onCutoffEnergyInelasticChanged)
        self._txt_cutoff_energy_bremsstrahlung.textChanged.connect(self._onCutoffEnergyBremsstrahlungChanged)
        self._txt_maximum_step_length.textChanged.connect(self._onMaximumStepLengthChanged)

        act_add_forcing.triggered.connect(self._onForcingAdd)
        act_remove_forcing.triggered.connect(self._onForcingRemove)

        return layout

    def _onElasticScatteringC1Changed(self):
        if self._txt_elastic_scattering_c1.hasAcceptableInput():
            self._txt_elastic_scattering_c1.setStyleSheet('background: none')
        else:
            self._txt_elastic_scattering_c1.setStyleSheet('background: pink')

    def _onElasticScatteringC2Changed(self):
        if self._txt_elastic_scattering_c2.hasAcceptableInput():
            self._txt_elastic_scattering_c2.setStyleSheet('background: none')
        else:
            self._txt_elastic_scattering_c2.setStyleSheet('background: pink')

    def _onCutoffEnergyInelasticChanged(self):
        if self._txt_cutoff_energy_inelastic.hasAcceptableInput():
            self._txt_cutoff_energy_inelastic.setStyleSheet('background: none')
        else:
            self._txt_cutoff_energy_inelastic.setStyleSheet('background: pink')

    def _onCutoffEnergyBremsstrahlungChanged(self):
        if self._txt_cutoff_energy_bremsstrahlung.hasAcceptableInput():
            self._txt_cutoff_energy_bremsstrahlung.setStyleSheet('background: none')
        else:
            self._txt_cutoff_energy_bremsstrahlung.setStyleSheet('background: pink')

    def _onMaximumStepLengthChanged(self):
        if self._txt_maximum_step_length.hasAcceptableInput():
            self._txt_maximum_step_length.setStyleSheet('background: none')
        else:
            self._txt_maximum_step_length.setStyleSheet('background: pink')

    def _onForcingAdd(self):
        index = self._tbl_forcing.selectionModel().currentIndex()
        model = self._tbl_forcing.model()
        model.insertRows(index.row() + 1)

    def _onForcingRemove(self):
        selection = self._tbl_forcing.selectionModel().selection().indexes()
        if len(selection) == 0:
            QMessageBox.warning(self, "Interaction forcing", "Select a row")
            return

        model = self._tbl_forcing.model()
        for row in sorted(map(methodcaller('row'), selection), reverse=True):
            model.removeRow(row)

    def _getParametersDict(self):
        params = _MaterialDialog._getParametersDict(self)

        params['c1'] = self._txt_elastic_scattering_c1.values().tolist()
        params['c2'] = self._txt_elastic_scattering_c2.values().tolist()

        wcc = self._txt_cutoff_energy_inelastic.values() * self._cb_cutoff_energy_inelastic.factor()
        params['wcc'] = wcc.tolist()

        wcr = self._txt_cutoff_energy_bremsstrahlung.values() * self._cb_cutoff_energy_bremsstrahlung.factor()
        params['wcr'] = wcr.tolist()

        dsmax = self._txt_maximum_step_length.values() * self._cb_maximum_step_length_unit.factor()
        params['dsmax'] = dsmax.tolist()

        params['forcings'] = \
            self._tbl_forcing.model().interaction_forcings()

        return params

    def _generateName(self, parameters, varied):
        name = parameters.pop('name')
        if name is None:
            name = Material.generate_name(parameters['composition'])

        parts = [name]
        for key in varied:
            if key == 'composition':
                continue
            elif key == 'forcings':
                forcing = parameters[key][0]
                forcer = forcing.forcer
                wlow = forcing.weight[0]
                whigh = forcing.weight[1]
                parts.append('forcings={0:n}_{1:n}_{2:n}'.format(forcer, wlow, whigh))
            else:
                parts.append('{0:s}={1:n}'.format(key, parameters[key]))
        return '+'.join(parts)

    def _createMaterial(self, parameters, varied):
        mat = _MaterialDialog._createMaterial(self, parameters, varied)

        c1 = parameters['c1']
        c2 = parameters['c2']
        wcc = parameters['wcc']
        wcr = parameters['wcr']
        dsmax = parameters['dsmax']
        forcings = parameters['forcings']

        return Material(mat.composition, mat.name, mat.density_kg_m3,
                        mat.absorption_energy_eV,
                        elastic_scattering=(c1, c2),
                        cutoff_energy_inelastic_eV=wcc,
                        cutoff_energy_bremsstrahlung_eV=wcr,
                        interaction_forcings=forcings,
                        maximum_step_length_m=dsmax)

    def setValue(self, material):
        _MaterialDialog.setValue(self, material)

        # Elastic scattering
        c1, c2 = material.elastic_scattering
        self._txt_elastic_scattering_c1.setValues(c1)
        self._txt_elastic_scattering_c2.setValues(c2)

        # Cutoff energy
        self._txt_cutoff_energy_inelastic.setValues(material.cutoff_energy_inelastic_eV)
        self._cb_cutoff_energy_inelastic.setUnit('eV')

        self._txt_cutoff_energy_bremsstrahlung.setValues(material.cutoff_energy_bremsstrahlung_eV)
        self._cb_cutoff_energy_bremsstrahlung.setUnit('eV')

        # Maximum step length
        self._txt_maximum_step_length.setValues(material.maximum_step_length_m)
        self._cb_maximum_step_length_unit.setUnit('m')

        # Interaction forcings
        forcings = material.interaction_forcings

        model = self._tbl_forcing.model()
        model.removeRows(0, model.rowCount())
        model.insertRows(1, len(forcings))

        for row, forcing in enumerate(forcings):
            model.setData(model.index(row, 0), forcing.particle)
            model.setData(model.index(row, 1), forcing.collision)
            model.setData(model.index(row, 2), forcing.forcer)
            model.setData(model.index(row, 3), forcing.weight[0])
            model.setData(model.index(row, 4), forcing.weight[1])

    def setReadOnly(self, state):
        _MaterialDialog.setReadOnly(self, state)

        style = 'color: none' if state else 'color: blue'
        self._lbl_elastic_scattering_c1.setStyleSheet(style)
        self._txt_elastic_scattering_c1.setReadOnly(state)

        self._lbl_elastic_scattering_c2.setStyleSheet(style)
        self._txt_elastic_scattering_c2.setReadOnly(state)

        self._lbl_cutoff_energy_inelastic.setStyleSheet(style)
        self._txt_cutoff_energy_inelastic.setReadOnly(state)
        self._cb_cutoff_energy_inelastic.setEnabled(not state)

        self._lbl_cutoff_energy_bremsstrahlung.setStyleSheet(style)
        self._txt_cutoff_energy_bremsstrahlung.setReadOnly(state)
        self._cb_cutoff_energy_bremsstrahlung.setEnabled(not state)

        self._lbl_maximum_step_length.setStyleSheet(style)
        self._txt_maximum_step_length.setReadOnly(state)
        self._cb_maximum_step_length_unit.setEnabled(not state)

        self._tbl_forcing.setEnabled(not state)
        self._tlb_forcing.setVisible(not state)

    def isReadOnly(self):
        return _MaterialDialog.isReadOnly(self) and \
            self._txt_elastic_scattering_c1.isReadOnly() and \
            self._txt_elastic_scattering_c2.isReadOnly() and \
            self._txt_cutoff_energy_inelastic.isReadOnly() and \
            self._txt_cutoff_energy_bremsstrahlung.isReadOnly() and \
            self._txt_maximum_step_length.isReadOnly() and \
            not self._tbl_forcing.isEnabled() and \
            not self._tlb_forcing.isVisible()

def __run():
    import sys
    from PySide.QtGui import QApplication

    material = Material({5: 0.5, 6: 0.5}, absorption_energy_eV={ELECTRON: 60.0},
                        elastic_scattering=(0.05, 0.1),
                        cutoff_energy_inelastic_eV=60.0,
                        cutoff_energy_bremsstrahlung_eV=70.0,
                        maximum_step_length_m=0.4,
                        interaction_forcings=[InteractionForcing(ELECTRON, DELTA, -2.0, (0.05, 0.6))])

    app = QApplication(sys.argv)

    dialog = MaterialDialog(None)
    dialog.setValue(material)
    if dialog.exec_():
        values = dialog.values()
        print(len(values))
        for value in values:
            print(repr(value))

    app.exec_()

#    print(widget.values())

if __name__ == '__main__':
    __run()
