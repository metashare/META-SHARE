"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""
from django import template

from metashare.repo2.models import corpusInfoType_model, \
    toolServiceInfoType_model, lexicalConceptualResourceInfoType_model, \
    languageDescriptionInfoType_model

register = template.Library()

class ResourceMediaTypes(template.Node):
    """
    Template tag that allows to obfuscate email addresses in page templates.
    
    Based on http://djangosnippets.org/snippets/1907/
    
    """
    
    def __init__(self, context_var):
        """
        Initialises this template tag.
        """
        super(ResourceMediaTypes, self).__init__()
        self.context_var = template.Variable(context_var)
        
    def render(self, context):
        """
        Renders a given email address as obfuscated JavaScript code.
        """
        result = []
        corpus_media = self.context_var.resolve(context)
    
        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            for corpus_info in media_type.corpustextinfotype_model_set.all():
                result.append(corpus_info.get_mediaType_display())
            if media_type.corpusAudioInfo:
                result.append(media_type.corpusAudioInfo \
                              .get_mediaType_display())
            for corpus_info in media_type.corpusvideoinfotype_model_set.all():
                result.append(corpus_info.get_mediaType_display())
            if media_type.corpusTextNgramInfo:
                result.append(media_type.corpusTextNgramInfo \
                              .get_mediaType_display())
            if media_type.corpusImageInfo:
                result.append(media_type.corpusImageInfo \
                              .get_mediaType_display())
            if media_type.corpusTextNumericalInfo:
                result.append(media_type.corpusTextNumericalInfo \
                              .get_mediaType_display())

        elif isinstance(corpus_media, lexicalConceptualResourceInfoType_model):
            lcr_media_type = corpus_media.lexicalConceptualResourceMediaType
            if lcr_media_type.lexicalConceptualResourceTextInfo:
                result.append(lcr_media_type.lexicalConceptualResourceTextInfo \
                              .get_mediaType_display())
            if lcr_media_type.lexicalConceptualResourceAudioInfo:
                result.append(lcr_media_type \
                    .lexicalConceptualResourceAudioInfo.get_mediaType_display())
            if lcr_media_type.lexicalConceptualResourceVideoInfo:
                result.append(lcr_media_type \
                    .lexicalConceptualResourceVideoInfo.get_mediaType_display())
            if lcr_media_type.lexicalConceptualResourceImageInfo:
                result.append(lcr_media_type \
                    .lexicalConceptualResourceImageInfo.get_mediaType_display())

        elif isinstance(corpus_media, languageDescriptionInfoType_model):
            ld_media_type = corpus_media.languageDescriptionMediaType
            if ld_media_type.languageDescriptionTextInfo:
                result.append(ld_media_type.languageDescriptionTextInfo \
                              .get_mediaType_display())
            if ld_media_type.languageDescriptionVideoInfo:
                result.append(ld_media_type.languageDescriptionVideoInfo \
                              .get_mediaType_display())
            if ld_media_type.languageDescriptionImageInfo:
                result.append(ld_media_type.languageDescriptionImageInfo \
                              .get_mediaType_display())

        elif isinstance(corpus_media, toolServiceInfoType_model):
            if corpus_media.inputInfo:
                result.extend(corpus_media.inputInfo \
                              .get_mediaType_display_list())
            if corpus_media.outputInfo:
                result.extend(corpus_media.outputInfo \
                              .get_mediaType_display_list())

        result = list(set(result))
        result.sort()
        
        media_list = ", ".join(result)
        
        return media_list

def resource_media_types(parser, token):
    """
    Use it like this: {% load_languages object.resourceComponentType %}
    """
    tokens = token.contents.split()
    if len(tokens) != 2:
        _msg = "%r tag accepts exactly two arguments" % tokens[0]
        raise template.TemplateSyntaxError(_msg)
    
    return ResourceMediaTypes(tokens[1])


register.tag('resource_media_types', resource_media_types)