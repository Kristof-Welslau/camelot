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
logger = logging.getLogger('camelot.view.controls.delegates.comboboxdelegate')

from .customdelegate import CustomDelegate, DocumentationMetaclass



from ....core.item_model import PreviewRole, FieldAttributesRole
from ....core.qt import Qt, variant_to_py, py_to_variant
from camelot.view.controls import editors

class ComboBoxDelegate(CustomDelegate, metaclass=DocumentationMetaclass):
    
    editor = editors.ChoicesEditor

    @classmethod
    def get_standard_item(cls, locale, model_context):
        item = super(ComboBoxDelegate, cls).get_standard_item(locale, model_context)
        choices = model_context.field_attributes.get('choices', [])
        for key, verbose in choices:
            if key == model_context.value:
                item.setData(py_to_variant(str(verbose)), PreviewRole)
                break
        else:
            if model_context.value is None:
                item.setData(py_to_variant(str()), PreviewRole)
            else:
                # the model has a value that is not in the list of choices,
                # still try to display it
                item.setData(py_to_variant(str(model_context.value)), PreviewRole)
        return item

    def setEditorData(self, editor, index):
        value = variant_to_py(index.data(Qt.ItemDataRole.EditRole))
        field_attributes = variant_to_py(index.data(FieldAttributesRole))
        editor.set_field_attributes(**(field_attributes or {}))
        editor.set_value(value)



