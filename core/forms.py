from django import forms
from django.contrib.auth import get_user_model


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), label='密码')
    confirm_password = forms.CharField(widget=forms.PasswordInput(), label='确认密码')
    
    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'password')
