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

from camelot.core.naming import initial_naming_context
from camelot.view.controls.delegates.customdelegate import CustomDelegate, DocumentationMetaclass

from dataclasses import dataclass, field
from typing import Any, ClassVar, List, Optional

from ....admin.admin_route import Route
from ....core.item_model import PreviewRole
from ....core.qt import Qt, qtranslate

@dataclass
class MonthsDelegate(CustomDelegate, metaclass=DocumentationMetaclass):
    """MonthsDelegate

    custom delegate for showing and editing months and years
    """

    minimum: int = 0
    maximum: int = 10000
    forever: int = None
    action_routes: List[Route] = field(default_factory=list)

    horizontal_align: ClassVar[Any] = Qt.AlignmentFlag.AlignRight

    @classmethod
    def get_editor_class(cls):
        return None

    @classmethod
    def value_to_string(cls, value, locale, field_attributes) -> Optional[str]:
        if value is not None:
            forever = field_attributes.get('forever', -2) or 0
            if value == forever:
                value_str = qtranslate('Forever')
            else:
                value_str = ''
                years, months = divmod(value, 12)
                if years!=0:
                    value_str = qtranslate('%n years', n=years) + ' '
                if months!=0:
                    value_str = value_str + qtranslate('%n months', n=months)
            return value_str

    @classmethod
    def get_standard_item(cls, locale, model_context):
        item = super().get_standard_item(locale, model_context)
        cls.set_item_editability(model_context, item, False)
        if model_context.value is not None:
            item.roles[Qt.ItemDataRole.EditRole] = initial_naming_context._bind_object(model_context.value)
            item.roles[PreviewRole] = cls.value_to_string(model_context.value, locale, model_context.field_attributes)
        return item
