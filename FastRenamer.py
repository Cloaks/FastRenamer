# Imports for UI functionality
import maya.OpenMayaUI
import PySide.QtCore as QtCore
import PySide.QtGui as QtGui
import pysideuic
import shiboken
import xml.etree.ElementTree as xml
from cStringIO import StringIO

# Import for the maya commands library
import maya.cmds as mc

# Extra imports
import os
import sys

VERSION = 0.1
WINDOWTITLE = "Fast Renamer"
WINDOWNAME = "fast_renamer"

# Standard strings to flag un-named items.
STANDARDPOLYS = ["pCube",
                 "pSphere",
                 "pCylinder", ]

STANDARDNURBS = ["nCircle", ]

STANDARDEXTRA = ["joint", ]

STANDARDNAMES = STANDARDPOLYS + STANDARDNURBS + STANDARDEXTRA


# Functions for PySide UI functionality in Maya
def get_pyside_class(ui_file):
    """
    Pablo Winant
    """
    parsed = xml.parse( ui_file )
    widget_class = parsed.find( 'widget' ).get( 'class' )
    form_class = parsed.find( 'class' ).text

    with open( ui_file, 'r' ) as f:
        o = StringIO()
        frame = {}

        pysideuic.compileUi( f, o, indent = 0 )
        pyc = compile( o.getvalue(), '<string>', 'exec' )
        exec pyc in frame

        # Fetch the base_class and form class based on their type in the xml from designer
        form_class = frame['Ui_{0}'.format( form_class )]
        base_class = eval( 'QtGui.{0}'.format( widget_class ) )

    return form_class, base_class


def wrapinstance(ptr, base=None):
    """
    Nathan Horne
    """
    if ptr is None:
        return None

    ptr = long( ptr ) #Ensure type
    if globals().has_key( 'shiboken' ):
        if base is None:
            qObj = shiboken.wrapInstance( long( ptr ), QtCore.QObject )
            metaObj = qObj.metaObject()
            cls = metaObj.className()
            superCls = metaObj.superClass().className()

            if hasattr( QtGui, cls ):
                base = getattr( QtGui, cls )

            elif hasattr( QtGui, superCls ):
                base = getattr( QtGui, superCls )

            else:
                base = QtGui.QWidget

        return shiboken.wrapInstance( long( ptr ), base )

    elif globals().has_key( 'sip' ):
        base = QtCore.QObject

        return sip.wrapinstance( long( ptr ), base )

    else:
        return None


def get_maya_window():
    maya_window_util = maya.OpenMayaUI.MQtUtil.mainWindow()
    maya_window = wrapinstance( long( maya_window_util ), QtGui.QWidget )

    return maya_window

TOOLPATH = os.path.dirname(__file__)
UI_FILE = os.path.join(TOOLPATH, "FastRenamerUI.ui")
UI_OBJECT, BASE_CLASS = get_pyside_class(UI_FILE)


# Main tool class
class FastRenamer(BASE_CLASS, UI_OBJECT):
    def __init__(self, parent=get_maya_window()):
        """
        Constructor for the UI

        Connect events like this:
                self.<OBJECT>.<EVENT>.connect( self.<METHOD> )
        """
        super(FastRenamer, self).__init__(parent)
        self.setupUi(self)  # inherited

        self.setWindowTitle("{0} - {1}".format(WINDOWTITLE, str(VERSION)))

        # History for entered names
        self._HISTORY = []
        self.renamelist = []

        print "-- NEW INSTANCE --"

        self.btn_meshes.clicked.connect(self.update_list)
        self.btn_joints.clicked.connect(self.update_list)
        self.btn_extras.clicked.connect(self.update_list)

        self.line_rename.returnPressed.connect(self.on_enter_press)

        # # Custom eventhandler for key-presses within QLineEdit
        # # https://gist.github.com/justinfx/3867879
        # self.line_rename.upPressed.connect(self.on_up_press)
        # self.line_rename.downPressed.connect(self.on_down_press)

        self.show()

    def update_list(self):
        buttonstate_meshes = self.btn_meshes.isChecked
        buttonstate_joints = self.btn_joints.isChecked
        buttonstate_extras = self.btn_extras.isChecked

        self.renamelist = []

        if buttonstate_meshes:
            meshlist = []
            for each in STANDARDPOLYS:
                meshlist.extend(mc.ls("{0}*".format(each), type="transform"))
                print "- Mesh list: ", meshlist
            self.renamelist.extend(meshlist)

        self.renamelist.append("Done")
        jointlist = []
        extralist = []

        self.line_rename.setText(self.renamelist[0])

    def on_enter_press(self):
        oldname = self.line_rename.text

        if oldname == "Done":
            raise Warning("Nothing to rename that with current filter-settings.")

        elif oldname == self.renamelist[0]:
            self.renamelist.pop(0)
            self.line_rename.setText(self.renamelist[0])

        elif not oldname:
            raise RuntimeError("Can't rename to an empty string.")

        else:
            mc.rename(self.renamelist[0], self.line_rename.text())
        print "- Rename list: ", self.renamelist
        print "-- ENTER --"

    # def on_up_press(self):
    #     print "-- UP --"
    #     raise NotImplementedError
    #
    # def on_down_press(self):
    #     raise NotImplementedError


# Function to show the UI
def show():
    """
    Checks if window is unique and if not, deletes and (re-)opens.
    """
    if mc.window(WINDOWNAME, exists=True, q=True):
        mc.deleteUI(WINDOWNAME)

    FastRenamer()