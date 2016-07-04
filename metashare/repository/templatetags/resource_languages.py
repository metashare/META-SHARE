from django import template

from metashare.repository.models import corpusInfoType_model, \
    toolServiceInfoType_model, lexicalConceptualResourceInfoType_model, \
    languageDescriptionInfoType_model

register = template.Library()

class ResourceLanguages(template.Node):
    """
    Template tag that allows to display languages in result page template.    
    """
    
    def __init__(self, context_var):
        """
        Initialises this template tag.
        """
        super(ResourceLanguages, self).__init__()
        self.context_var = template.Variable(context_var)
        
    def render(self, context):
        """
        Renders languages.
        """
        result = []
        corpus_media = self.context_var.resolve(context)
    
        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            for corpus_info in media_type.corpustextinfotype_model_set.all():
                result.extend([lang.languageName for lang in
                               corpus_info.languageinfotype_model_set.all()])
            if media_type.corpusAudioInfo:
                result.extend([lang.languageName for lang in
                               media_type.corpusAudioInfo.languageinfotype_model_set.all()])
            for corpus_info in media_type.corpusvideoinfotype_model_set.all():
                result.extend([lang.languageName for lang in
                               corpus_info.languageinfotype_model_set.all()])
            if media_type.corpusTextNgramInfo:
                result.extend([lang.languageName for lang in
                            media_type.corpusTextNgramInfo.languageinfotype_model_set.all()])
            if media_type.corpusImageInfo:
                result.extend([lang.languageName for lang in
                               media_type.corpusImageInfo.languageinfotype_model_set.all()])

        elif isinstance(corpus_media, lexicalConceptualResourceInfoType_model):
            lcr_media_type = corpus_media.lexicalConceptualResourceMediaType
            if lcr_media_type.lexicalConceptualResourceAudioInfo:
                result.extend([lang.languageName for lang in lcr_media_type \
                        .lexicalConceptualResourceAudioInfo.languageinfotype_model_set.all()])
            if lcr_media_type.lexicalConceptualResourceTextInfo:
                result.extend([lang.languageName for lang in lcr_media_type \
                        .lexicalConceptualResourceTextInfo.languageinfotype_model_set.all()])
            if lcr_media_type.lexicalConceptualResourceVideoInfo:
                result.extend([lang.languageName for lang in lcr_media_type \
                        .lexicalConceptualResourceVideoInfo.languageinfotype_model_set.all()])
            if lcr_media_type.lexicalConceptualResourceImageInfo:
                result.extend([lang.languageName for lang in lcr_media_type \
                        .lexicalConceptualResourceImageInfo.languageinfotype_model_set.all()])

        elif isinstance(corpus_media, languageDescriptionInfoType_model):
            ld_media_type = corpus_media.languageDescriptionMediaType
            if ld_media_type.languageDescriptionTextInfo:
                result.extend([lang.languageName for lang in ld_media_type \
                            .languageDescriptionTextInfo.languageinfotype_model_set.all()])
            if ld_media_type.languageDescriptionVideoInfo:
                result.extend([lang.languageName for lang in ld_media_type \
                            .languageDescriptionVideoInfo.languageinfotype_model_set.all()])
            if ld_media_type.languageDescriptionImageInfo:
                result.extend([lang.languageName for lang in ld_media_type \
                            .languageDescriptionImageInfo.languageinfotype_model_set.all()])

        elif isinstance(corpus_media, toolServiceInfoType_model):
            if corpus_media.inputInfo:
                result.extend(corpus_media.inputInfo.languageName)
            if corpus_media.outputInfo:
                result.extend(corpus_media.outputInfo.languageName)

        result = list(set(result))
        result.sort()

        return u"".join(u"<li class=\"languages\">{}</li>".format(lang) for lang in result)

def resource_languages(parser, token):
    """
    Use it like this: {% load_languages object.resourceComponentType.as_subclass %}
    """
    tokens = token.contents.split()
    if len(tokens) != 2:
        _msg = "%r tag accepts exactly two arguments" % tokens[0]
        raise template.TemplateSyntaxError(_msg)
    
    return ResourceLanguages(tokens[1])


register.tag('resource_languages', resource_languages)
