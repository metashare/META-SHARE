
from django import template

register = template.Library()

def toFieldName(value): 
    str_list = value.split(' ')
    if str_list.__len__() == 0:
        return ''
    new_value = str_list[0].lower()
    for str in str_list[1:]:
        new_value = new_value + str[0].upper() + str[1:]
        
    return new_value

register.filter('toFieldName', toFieldName)
