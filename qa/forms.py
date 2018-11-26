from django import forms
from django.conf import settings
from qa.models import Question

from django.forms import widgets as wid  #因为重名，所以起个别名
    

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['title', 'description', 'tags']
        '''labels = {
                                    'title':'标题',
                                    'description':'内容',
                                    'tags':'标签',
                                }'''
        # widgets = {
        #     "title":wid.TextInput(attrs={
        #         'placeholder':'问题简称',
        #         'class':'form-control',
        #         'width': '30%',
        #         }),
        #     "description":wid.Textarea(attrs={
        #         'placeholder':'开始提问吧',
        #         #'class':'form-control',
        #         'class':"form-control",
        #         'rows':'3'
        #         }),
        #     # "tags":wid.EmailInput(attrs={'class':'form-control'})
        # }
 
    def __init__(self, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)

        try:
            settings.QA_SETTINGS['qa_description_optional']
            self.fields['description'].required = not settings.QA_SETTINGS[
                'qa_description_optional']

        except KeyError:
            pass
