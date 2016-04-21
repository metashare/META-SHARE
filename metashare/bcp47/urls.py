from django.conf.urls import patterns, url

urlpatterns = patterns('metashare.bcp47.xhr',
    url(r'^xhr/update_lang_variants/$', 'update_lang_variants'),
    url(r'^xhr/update_var_variants/$', 'update_var_variants'),
    url(r'^xhr/update_lang_variants_with_script/$', 'update_lang_variants_with_script'),
)