"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""
from django import template
from metashare.settings import MEDIA_URL

register = template.Library()

class GetIcon(template.Node):
    """
    Template tag that allows to display an icon in result page template.    
    """
    
    def __init__(self, context_var):
        """
        Initialises this template tag.
        """
        super(GetIcon, self).__init__()
        self.context_var = template.Variable(context_var)
        
    def render(self, context):
       
        result = self.context_var.resolve(context)
        # use images instead of plain text when displaying media types
        image_tag = ""
        if result == "text":
            image_tag = ' <img title="text" src="{}css/sexybuttons/images/icons/silk/page' \
              '_white_text_media_type.png" /> &nbsp;' \
              .format(MEDIA_URL)
        if result == "audio":
            image_tag = image_tag + ' <img title="audio" src="{}css/sexybuttons/images/' \
              'icons/silk/sound_none.png" /> &nbsp; ' \
              .format(MEDIA_URL)
        if result == "image":
            image_tag = image_tag + ' <img title="image" src="{}css/sexybuttons/images/' \
              'icons/silk/picture.png" /> &nbsp; ' \
              .format(MEDIA_URL)
        if result == "video":
            image_tag = image_tag + ' <img title="video" src="{}css/sexybuttons/images/' \
              'icons/silk/film.png" />' \
              .format(MEDIA_URL)
        if result == "textNumerical":
            image_tag = image_tag + ' <img title="textNumerical" src="{}css/sexybuttons/images/' \
              'icons/silk/eye.png" />' \
              .format(MEDIA_URL)
        if result == "textNgram":
            image_tag = image_tag + ' <img title="textNgram" src="{}css/sexybuttons/images/' \
              'icons/silk/text_align_left.png" />' \
              .format(MEDIA_URL)              
        if result == "corpus":
            image_tag = image_tag + ' <img title="Corpus" src="{}css/sexybuttons/images/' \
              'icons/silk/database_yellow.png" />' \
              .format(MEDIA_URL)
              
        if result == "toolService":
            image_tag = image_tag + ' <img title="Tool/Service" src="{}css/sexybuttons/images/' \
              'icons/silk/page_white_gear.png" />' \
              .format(MEDIA_URL)
              
        if result == "lexicalConceptualResource":
            image_tag = image_tag + ' <img title="Lexical Conceptual" src="{}css/sexybuttons/images/' \
              'icons/silk/text_ab.png" />' \
              .format(MEDIA_URL)
              
        if result == "languageDescription":
            image_tag = image_tag + ' <img title="Language Description" src="{}css/sexybuttons/images/' \
              'icons/silk/script.png" />' \
              .format(MEDIA_URL)
        
        if result == "male":
            image_tag = image_tag + ' <img title="Male" src="{}css/sexybuttons/images/' \
              'icons/silk/male.png" />' \
              .format(MEDIA_URL)
        
        if result == "female":
            image_tag = image_tag + ' <img title="Female" src="{}css/sexybuttons/images/' \
              'icons/silk/female.png" />' \
              .format(MEDIA_URL)
        
        return image_tag

def get_icon(parser, token):
    """
    Use it like this: {% get_icon variable %}
    """
    tokens = token.contents.split()
    if len(tokens) != 2:
        _msg = "%r tag accepts exactly two arguments" % tokens[0]
        raise template.TemplateSyntaxError(_msg)
    
    return GetIcon(tokens[1])


register.tag('get_icon', get_icon)
