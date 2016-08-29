import logging

from django.test import TestCase
from metashare.local_settings import DJANGO_BASE
from metashare.settings import LOG_HANDLER

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(LOG_HANDLER)


class Bcp47Tests(TestCase):
    @classmethod
    def setUpClass(cls):
        LOGGER.info("running '{}' tests...".format(cls.__name__))

    @classmethod
    def tearDownClass(cls):
        LOGGER.info("finished '{}' tests".format(cls.__name__))

    # update variants by language
    def test_update_lang_variants(self):
        result = "Boontling//Early Modern English (1500-1700)//Scottish Standard English//" \
                 "Scouse//Unifon phonetic alphabet//ALA-LC Romanization, 1997 edition//" \
                 "International Phonetic Alphabet//Uralic Phonetic Alphabet//X-SAMPA transcription"
        post_data = {'lang': 'English'}
        response = self.client.post('/{0}bcp47/xhr/update_lang_variants/'.format(DJANGO_BASE),
                                    post_data)
        self.assertEquals(response.content, result)

    # update variants by a previously given variant
    def test_update_var_variants(self):
        result = "ALA-LC Romanization, 1997 edition//International Phonetic Alphabet" \
                 "//Uralic Phonetic Alphabet//X-SAMPA transcription"
        post_data = {'variant': 'Boontling'}
        response = self.client.post('/{0}bcp47/xhr/update_var_variants/'.format(DJANGO_BASE),
                                    post_data)
        self.assertEquals(response.content, result)

    # update variants by language and script
    def test_update_lang_variants_with_script(self):
        result = "ALA-LC Romanization, 1997 edition//Boontling//Early Modern English (1500-1700)" \
                 "//International Phonetic Alphabet//Scottish Standard English//Scouse" \
                 "//Unifon phonetic alphabet//Uralic Phonetic Alphabet//X-SAMPA transcription"
        post_data = {'lang': 'English', 'script': 'Greek'}
        response = self.client.post('/{0}bcp47/xhr/update_lang_variants_with_script/'.format(DJANGO_BASE),
                                    post_data)
        self.assertEquals(response.content, result)
