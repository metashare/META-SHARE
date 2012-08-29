"""
String utility methods to be used in templates.
"""

from django import template

register = template.Library()



def to_field_name(value): 
    """
    This template tag is used to convert a list of words
    into a single word that does not contain spaces.
    The words are capitalized as they are joined.
    It is used in some templates to get the correct
    knowledge base link for fields or components.
    Es. 'text classificationInfo' is converted into 'textClassificationInfo'
    """
    str_list = value.split(' ')
    if str_list.__len__() == 0:
        return ''
    new_value = str_list[0].lower()
    for str_item in str_list[1:]:
        new_value = new_value + str_item[0].upper() + str_item[1:]
        
    return new_value

register.filter('to_field_name', to_field_name)
