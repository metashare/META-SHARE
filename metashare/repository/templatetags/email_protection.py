"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""
from django import template
from random import randrange, shuffle

register = template.Library()


class EncryptEmail(template.Node):
    """
    Template tag that allows to obfuscate email addresses in page templates.
    
    Based on http://djangosnippets.org/snippets/1907/
    
    """
    
    def __init__(self, context_var):
        """
        Initialises this template tag.
        """
        super(EncryptEmail, self).__init__()
        self.context_var = template.Variable(context_var)
    
    def render(self, context):
        """
        Renders a given email address as obfuscated JavaScript code.
        """
        email_address = self.context_var.resolve(context)
        email_id = 'e' + str(randrange(1, 999999999))
        
        character_set = '+-.0123456789@ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghi' \
          'jklmnopqrstuvwxyz'
        character_list = list(character_set)
        shuffle(character_list)
        
        key = ''.join(character_list)
        
        crypted = ''.join([key[character_set.find(c)] for c in email_address])
        
        # Create JavaScript-based, obfuscated email address representation.
        script = 'var a="{}";var b=a.split("").sort().join("");var c="{}";' \
          'var d="";for(var e=0;e<c.length;e++)d+=b.charAt(a.indexOf(c.cha' \
          'rAt(e)));document.getElementById("{}").innerHTML="<a href=\\"ma' \
          'ilto:"+d+"\\">"+d+"</a>"'.format(key, crypted, email_id)
        
        script = script.replace("\\","\\\\").replace('"','\\"')
        
        obfuscated = '<span id="{}">[javascript protected email address]</' \
          'span><script type="text/javascript">/*<![CDATA[*/eval("{}")/*]]' \
          '>*/</script>'.format(email_id, script)
        
        return obfuscated


def encrypt_email(parser, token):
    """
    Use it like this: {% encrypt_email user.email %}
    """
    tokens = token.contents.split()
    if len(tokens) != 2:
        _msg = "%r tag accepts exactly two arguments" % tokens[0]
        raise template.TemplateSyntaxError(_msg)
    
    return EncryptEmail(tokens[1])


register.tag('encrypt_email', encrypt_email)