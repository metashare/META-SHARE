'''
Created on 28/feb/2012

@author: Salvatore Minutoli
'''

from django import forms
from django.core.exceptions import ValidationError
from metashare.repository.models import corpusAudioInfoType_model
from metashare.repository.models import audioSizeInfoType_model
from metashare.repository.models import sizeInfoType_model
from metashare.repository.models import durationOfAudioInfoType_model
from metashare.repository.models import durationOfEffectiveSpeechInfoType_model
from metashare.repository.models import SIZEINFOTYPE_SIZEUNIT_CHOICES
from metashare.repository.models import DURATIONOFAUDIOINFOTYPE_DURATIONUNIT_CHOICES
from metashare.repository.models import DURATIONOFEFFECTIVESPEECHINFOTYPE_DURATIONUNIT_CHOICES

class CorpusAudioForm(forms.ModelForm):
    audio_size_1 = forms.IntegerField(required=True,
      label='Audio size 1')
    audio_size_unit_1 = forms.ChoiceField(required=True,
      choices=SIZEINFOTYPE_SIZEUNIT_CHOICES['choices'],
      label='Audio size unit 1')
    duration_effective_1 = forms.IntegerField(required=False,
    label='Duration of Effective Speech 1')
    duration_effective_unit_1 = forms.ChoiceField(required=False,
      choices=DURATIONOFAUDIOINFOTYPE_DURATIONUNIT_CHOICES['choices'],
      label='Duration of Effective Speech unit 1')
    duration_audio_1 = forms.IntegerField(required=False,
      label='Duration of Audio 1')
    duration_audio_unit_1 = forms.ChoiceField(required=False,
      choices=DURATIONOFEFFECTIVESPEECHINFOTYPE_DURATIONUNIT_CHOICES['choices'],
      label='Duration of Audio unit 1')
    
    audio_size_2 = forms.IntegerField(required=False,
      label='Audio size 2')
    audio_size_unit_2 = forms.ChoiceField(required=False,
      choices=SIZEINFOTYPE_SIZEUNIT_CHOICES['choices'],
      label='Audio size unit 2')
    duration_effective_2 = forms.IntegerField(required=False,
      label='Duration of Effective Speech 2')
    duration_effective_unit_2 = forms.ChoiceField(required=False,
      choices=DURATIONOFAUDIOINFOTYPE_DURATIONUNIT_CHOICES['choices'],
      label='Duration of Effective Speech unit 2')
    duration_audio_2 = forms.IntegerField(required=False,
      label='Duration of Audio 2')
    duration_audio_unit_2 = forms.ChoiceField(required=False,
      choices=DURATIONOFEFFECTIVESPEECHINFOTYPE_DURATIONUNIT_CHOICES['choices'],
      label='Duration of Audio unit 2')
    
    class Meta:
        model = corpusAudioInfoType_model
        
    def __init__(self, *args, **kwargs):
        super(CorpusAudioForm, self).__init__(*args, **kwargs)
        if self.instance:
            audio_sizes_mngr = self.instance.audiosizeinfotype_model_set
            audio_sizes_num = audio_sizes_mngr.count()
            audio_sizes = audio_sizes_mngr.all()
            for i in xrange(0, 2):
                if audio_sizes_num > i:
                    audio_size = audio_sizes[i]
                    self.display_audio_size(audio_size, i + 1)
    
    def display_audio_size(self, audio_size, index):
        size_infos = audio_size.sizeInfo.all()
        if size_infos.count() > 0:
            size_info = size_infos[0]
            size = size_info.size
            size_unit = size_info.sizeUnit
            name1 = u'audio_size_%d' % (index)
            name2 = u'audio_size_unit_%d' % (index)
            self.initial.update({name1: size, name2: size_unit})
        dur_effs_mngr = audio_size.durationofeffectivespeechinfotype_model_set
        dur_effs_num = dur_effs_mngr.count()
        dur_effs = dur_effs_mngr.all()
        if dur_effs_num > 0:
            dur_eff = dur_effs[0]
            dur_eff_size = dur_eff.size
            dur_eff_unit = dur_eff.durationUnit
            name1 = 'duration_effective_%d' % (index)
            name2 = 'duration_effective_unit_%d' % (index)
            self.initial.update({name1: dur_eff_size, name2: dur_eff_unit})
        dur_audios_mngr = audio_size.durationofaudioinfotype_model_set
        dur_audios_num = dur_audios_mngr.count()
        dur_audios = dur_audios_mngr.all()
        if dur_audios_num > 0:
            dur_audio = dur_audios[0]
            dur_audio_size = dur_audio.size
            dur_audio_unit = dur_audio.durationUnit
            name1 = 'duration_audio_%d' % (index)
            name2 = 'duration_audio_unit_%d' % (index)
            self.initial.update({name1: dur_audio_size, name2: dur_audio_unit})
    
    def save(self, *args, **kwargs):
        print 'CorpusAudio: saving data'
        result = super(CorpusAudioForm, self).save(*args, **kwargs)
        #self.save_audio_sizes(**kwargs)
        return result
    
    def save_audio_sizes(self, commit=True):
        if self.instance:
            if self.instance.id is None:
                self.instance.save()
            audio_sizes_mngr = self.instance.audiosizeinfotype_model_set
            audio_sizes_num = audio_sizes_mngr.count()
            audio_sizes = audio_sizes_mngr.all()
            
            for i in xrange(0, 2):
                if audio_sizes_num > i:
                    audio_size = audio_sizes[i]
                else:
                    audio_size = audioSizeInfoType_model()
                    audio_size.back_to_corpusaudioinfotype_model = self.instance
                    # must have an ID before adding a sizeInfo
                    audio_size.save()
                index = i + 1
                name = u'audio_size_%d' % (index)
                audio_size_value = self.cleaned_data.get(name)
                name = u'audio_size_unit_%d' % (index)
                audio_size_unit_value = self.cleaned_data.get(name)
                name = u'duration_effective_%d' % (index)
                duration_effective_value = self.cleaned_data.get(name)
                name = u'duration_effective_unit_%d' % (index)
                duration_effective_unit_value = self.cleaned_data.get(name)
                name = u'duration_audio_%d' % (index)
                duration_audio_value = self.cleaned_data.get(name)
                name = u'duration_audio_unit_%d' % (index)
                duration_audio_unit_value = self.cleaned_data.get(name)
                self.save_audio_size(audio_size, audio_size_value, audio_size_unit_value,
                                     duration_effective_value, duration_effective_unit_value,
                                     duration_audio_value, duration_audio_unit_value,
                                     commit)
                
    
    def save_audio_size(self, audio_size, audio_size_value, audio_size_unit_value,
                        duration_effective_value, duration_effective_unit_value,
                        duration_audio_value, duration_audio_unit_value, commit):
        size_infos = audio_size.sizeInfo.all()
        if audio_size_value is not None:
            if size_infos.count() > 0:
                size_info = size_infos[0]
            else:
                size_info = sizeInfoType_model()
        else:
            if size_infos.count() > 0:
                size_info = size_infos[0]
                size_info.delete()
            return
            
        size_info.size = audio_size_value
        size_info.sizeUnit = audio_size_unit_value
        size_info.save()
        audio_size.back_to_corpusaudioinfotype_model = self.instance
        # must have an ID before adding a sizeInfo
        audio_size.save()
        audio_size.sizeInfo.add(size_info)
        audio_size.save()
        dur_effs_mngr = audio_size.durationofeffectivespeechinfotype_model_set
        dur_effs_num = dur_effs_mngr.count()
        dur_effs = dur_effs_mngr.all()
        if duration_effective_value is not None:
            if dur_effs_num > 0:
                dur_eff = dur_effs[0]
            else:
                dur_eff = durationOfEffectiveSpeechInfoType_model()
            dur_eff.size = duration_effective_value
            dur_eff.durationUnit = duration_effective_unit_value
            dur_eff.back_to_audiosizeinfotype_model = audio_size
            dur_eff.save()
        else:
            if dur_effs_num > 0:
                dur_eff = dur_effs[0]
                dur_eff.delete()
                
        dur_audios_mngr = audio_size.durationofaudioinfotype_model_set
        dur_audios_num = dur_audios_mngr.count()
        dur_audios = dur_audios_mngr.all()
        if duration_audio_value is not None:
            if dur_audios_num > 0:
                dur_audio = dur_audios[0]
            else:
                dur_audio = durationOfAudioInfoType_model()
            dur_audio.size = duration_audio_value
            dur_audio.durationUnit = duration_audio_unit_value
            dur_audio.back_to_audiosizeinfotype_model = audio_size
            dur_audio.save()
        else:
            if dur_audios_num > 0:
                dur_audio = dur_audios[0]
                dur_audio.delete()
    
    def is_valid(self):
        valid = super(CorpusAudioForm, self).is_valid()
        #if one of duration_effective and duration_audio of the
        #second AudioSizeInfo are not None then size_info.size is required
        if valid:
            index = 2
            name = u'duration_effective_%d' % (index)
            duration_effective_value = self.cleaned_data.get(name)
            name = u'duration_audio_%d' % (index)
            duration_audio_value = self.cleaned_data.get(name)
            if duration_effective_value is not None or \
               duration_audio_value is not None:
                name = u'audio_size_%d' % (index)
                audio_size_value = self.cleaned_data.get(name)
                if audio_size_value is None:
                    valid = False
                    e = ValidationError('This field is required')
                    self._errors[name] = self.error_class(e.messages)
            
        return valid
