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
        character_set = '+-.0123456789@ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghi' \
          'jklmnopqrstuvwxyz'
        character_list = list(character_set)
        shuffle(character_list)
        
        key = ''.join(character_list)
        
        cipher_text = ''
        _id = 'e' + str(randrange(1, 999999999))
        
        for character in email_address:
            cipher_text += key[character_set.find(character)]
        
        script = 'var a="'+key+'";var b=a.split("").sort().join("");var c="'+cipher_text+'";var d="";'
        script += 'for(var e=0;e<c.length;e++)d+=b.charAt(a.indexOf(c.charAt(e)));'
        script += 'document.getElementById("'+_id+'").innerHTML="<a href=\\"mailto:"+d+"\\">"+d+"</a>"'
        
        script = "eval(\""+ script.replace("\\","\\\\").replace('"','\\"') + "\")"
        script = '<script type="text/javascript">/*<![CDATA[*/'+script+'/*]]>*/</script>'
        
        return '<span id="'+ _id + '">[javascript protected email address]</span>'+ script


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