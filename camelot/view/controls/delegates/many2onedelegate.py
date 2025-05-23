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

from dataclasses import dataclass, field
from typing import List, Optional
import logging

from ....admin.admin_route import Route
from ....core.naming import initial_naming_context
from ....core.qt import Qt
from ....core.item_model import PreviewRole, CompletionsRole
from .customdelegate import CustomDelegate, DocumentationMetaclass

logger = logging.getLogger(__name__)

@dataclass
class Many2OneDelegate(CustomDelegate, metaclass=DocumentationMetaclass):
    """Custom delegate for many 2 one relations

  .. image:: /_static/manytoone.png

  Once an item has been selected, it is represented by its unicode representation
  in the editor or the table.  So the related classes need an implementation of
  their __str__ method.
  """

    action_routes: List[Route] = field(default_factory=list)

    def __post_init__(self, parent):
        logger.debug('create many2onecolumn delegate')
        super().__post_init__(parent)
        self._width = self._width * 2

    @classmethod
    def get_editor_class(cls):
        return None

    @classmethod
    def value_to_string(cls, value, locale, field_attributes) -> Optional[str]:
        if value is not None:
            admin = field_attributes['admin']
            try:
                verbose_name = admin.get_verbose_object_name(value)
            except Exception as e:
                verbose_name = ''
                logger.error(
                    'Could not call get_verbose_object_name on {}'.format(type(admin).__name__),
                    exc_info=e
                )
            return verbose_name

    @classmethod
    def get_standard_item(cls, locale, model_context):
        item = super().get_standard_item(locale, model_context)
        cls.set_item_editability(model_context, item, False)
        value_name = initial_naming_context._bind_object(model_context.value)
        # eventually, all values should be names, so this should happen in the
        # custom delegate class
        item.roles[Qt.ItemDataRole.EditRole] = value_name
        if model_context.value is not None:
            item.roles[PreviewRole] = cls.value_to_string(model_context.value, locale, model_context.field_attributes)
        return item

    def setEditorData(self, editor, index):
        if index.model() is None:
            return
        # either an update signal is received because there are search
        # completions, or because the value of the editor needs to change
        #prefix = index.model().data(index, CompletionPrefixRole)
        completions = index.model().data(index, CompletionsRole)
        if completions is not None:
            editor.display_search_completions(completions)
            return
        super().setEditorData(editor, index)
        verbose_name = index.model().data(index, PreviewRole)
        editor.set_verbose_name(verbose_name)
