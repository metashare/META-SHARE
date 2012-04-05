"""
Project: META-SHARE prototype implementation
 Author: Christian Spurk <cspurk@dfki.de>
"""
from haystack.exceptions import SearchFieldError
from haystack.indexes import SearchField, CharField, MultiValueField

class LabeledField(SearchField):
    """
    A kind of mixin class for creating `SearchField`s with a label.
    """
    def __init__(self, label, **kwargs):
        if label is None:
            raise SearchFieldError("'{0}' fields must have a label." \
                                   .format(self.__class__.__name__))
        self.label = label
        super(LabeledField, self).__init__(**kwargs)

class LabeledCharField(LabeledField, CharField):
    """
    A `CharField` with a label.
    """
    pass

class LabeledMultiValueField(LabeledField, MultiValueField):
    """
    A `MultiValueField` with a label.
    """
    pass
