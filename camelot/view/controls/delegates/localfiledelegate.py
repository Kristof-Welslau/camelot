#  ============================================================================
#
#  Copyright (C) 2007-2013 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / info@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file license.txt included in the packaging of
#  this file.  Please review this information to ensure GNU
#  General Public Licensing requirements will be met.
#
#  If you are unsure which license is appropriate for your use, please
#  visit www.python-camelot.com or contact info@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  info@conceptive.be
#
#  ============================================================================

import logging
logger = logging.getLogger('camelot.view.controls.delegates.localfiledelegate')

from PyQt4.QtCore import Qt

import six

from .customdelegate import CustomDelegate
from .customdelegate import DocumentationMetaclass

from camelot.core.utils import variant_to_pyobject

from camelot.view.controls import editors
from camelot.view.proxy import ValueLoading

class LocalFileDelegate( six.with_metaclass( DocumentationMetaclass,
                                             CustomDelegate ) ):
    """Delegate for displaying a path on the local file system.  This path can
    either point to a file or a directory
    """

    editor = editors.LocalFileEditor

    def __init__(
        self, 
        parent=None,
        **kw
    ):
        CustomDelegate.__init__(self, parent, **kw)

    def paint(self, painter, option, index):
        painter.save()
        self.drawBackground(painter, option, index)
        value = variant_to_pyobject( index.model().data( index, Qt.EditRole ) )
        
        value_str = u''
        if value not in (None, ValueLoading):
            value_str = six.text_type(value)

        self.paint_text(painter, option, index, value_str)
        painter.restore()



