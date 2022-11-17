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

import logging
logger = logging.getLogger('camelot.view.controls.delegates.plaintextdelegate')



from ....core.item_model import PreviewRole
from ....core.qt import py_to_variant
from .customdelegate import CustomDelegate
from .customdelegate import DocumentationMetaclass
from camelot.core.qt import QtWidgets

from camelot.view.controls import editors

DEFAULT_COLUMN_WIDTH = 20

class PlainTextDelegate(CustomDelegate, metaclass=DocumentationMetaclass):
    """Custom delegate for simple string values"""

    def __init__( self,
                  parent = None,
                  length = DEFAULT_COLUMN_WIDTH,
                  translate_content=False,
                  **kw ):
        CustomDelegate.__init__( self, parent, length = length, **kw )
        self._translate_content = translate_content
        char_width = self._font_metrics.averageCharWidth()
        self._width = char_width * min( DEFAULT_COLUMN_WIDTH, length or DEFAULT_COLUMN_WIDTH )

    @classmethod
    def get_editor_class(cls):
        return editors.TextLineEditor

    @classmethod
    def get_standard_item(cls, locale, model_context):
        completer = model_context.field_attributes.get('completer')
        if completer is not None:
            completer.moveToThread(QtWidgets.QApplication.instance().thread())
        item = super(PlainTextDelegate, cls).get_standard_item(locale, model_context)
        if model_context.value is not None:
            item.setData(py_to_variant(str(model_context.value)), PreviewRole)
        return item



