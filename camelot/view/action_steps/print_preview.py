#  ============================================================================
#
#  Copyright (C) 2007-2016 Conceptive Engineering bvba.
#  www.conceptive.be / info@conceptive.be
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of Conceptive Engineering nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  ============================================================================
from dataclasses import dataclass

from ...core.qt import QtCore, QtGui, QtPrintSupport

from camelot.admin.action import ActionStep
from camelot.view.action_steps.open_file import OpenFile
from camelot.view.action_runner import hide_progress_dialog
from camelot.view.utils import resize_widget_to_screen

@dataclass
class PrintPreview( ActionStep ):
    """
    Display a print preview dialog box.
    
    :param document: an instance of :class:`QtGui.QTextDocument`
        that has a :meth:`print_` method.  The thread affinity of this object
        will be changed to be able to use it in the GUI.

    the print preview can be customised using these attributes :
    
    .. attribute:: margin_left

        change the left margin of the content to the page border, unit is set by margin_unit

    .. attribute:: margin_top

        change the top margin of the content to the page border, unit is set by margin_unit    

    .. attribute:: margin_right

        change the right margin of the content to the page border, unit is set by margin_unit

    .. attribute:: margin_bottom

        change the bottom margin of the content to the page border, unit is set by margin_unit

    .. attribute:: margin_unit

        defin which unit is used for the defined margins (e.g. margin_left, margin_bottom)

    .. attribute:: page_size
    
        the page size, by default :class:`QtGui.QPageSize(QtGui.QPageSize.PageSizeId.A4)` is used
    
    .. attribute:: page_orientation
    
        the page orientation, by default :class:`QtPrintSupport.QPrinter.Orientation.Portrait`
        is used.
        
    .. attribute:: document
        
        the :class:`QtGui.QTextDocument` holding the document that will be shown in the print
        preview
        
    .. attribute:: actions
    
        the list of additional document actions to be displayed in the toolbar of the
        print preview
    
    .. image:: /_static/simple_report.png
        """

    document: QtGui.QTextDocument
    
    def __post_init__(self):
        self.document.moveToThread( QtCore.QCoreApplication.instance().thread() )
        self.printer = None
        self.margin_left = None
        self.margin_top = None
        self.margin_right = None
        self.margin_bottom = None
        self.margin_unit = QtPrintSupport.QPrinter.Unit.Millimeter
        self.page_size = None
        self.page_orientation = None

    def get_printer(self):
        if self.printer is not None:
            return self.printer
        printer = QtPrintSupport.QPrinter()
        if not printer.isValid():
            printer.setOutputFormat( QtPrintSupport.QPrinter.OutputFormat.PdfFormat )
        return printer

    def config_printer(self, printer):
        if self.page_size is not None:
            printer.setPageSize( self.page_size )
        if self.page_orientation is not None:
            printer.setOrientation( self.page_orientation )
        if None not in [self.margin_left, self.margin_top, self.margin_right, self.margin_bottom, self.margin_unit]:
            printer.setPageMargins( self.margin_left, self.margin_top, self.margin_right, self.margin_bottom, self.margin_unit )

    def paint_on_printer( self, printer ):
        self.document.print(printer)

    def render( self, gui_context ):
        """create the print preview widget. this method is used to unit test
        the action step."""
        printer = self.get_printer()
        self.config_printer(printer)
        dialog = QtPrintSupport.QPrintPreviewDialog(
            printer, flags = QtCore.Qt.WindowType.Window
        )
        dialog.printer = printer
        dialog.paintRequested.connect( self.paint_on_printer )
        # show maximized seems to trigger a bug in qt which scrolls the page 
        # down dialog.showMaximized()
        resize_widget_to_screen( dialog )
        return dialog
     
    def gui_run( self, gui_context ):
        dialog = self.render( gui_context )
        with hide_progress_dialog( gui_context ):
            dialog.exec()
        
    def get_pdf(self, filename=None):
        printer = QtPrintSupport.QPrinter()
        printer.setOutputFormat(QtPrintSupport.QPrinter.OutputFormat.PdfFormat)
        self.config_printer(printer)
        if filename is None:
            filename = OpenFile.create_temporary_file('.pdf')
        printer.setOutputFileName(filename)
        self.paint_on_printer(printer)
        return filename
