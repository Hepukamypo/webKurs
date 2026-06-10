from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Game, Review, Screenshot, Achievement

BS        = {'class': 'form-control'}
BS_SELECT = {'class': 'form-select'}


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email',
                             widget=forms.EmailInput(attrs=BS))
    role  = forms.ChoiceField(
                label='Я регистрируюсь как',
                choices=[('player', 'Игрок'), ('developer', 'Разработчик')],
                widget=forms.RadioSelect(),
                initial='player')

    class Meta:
        model  = User
        fields = ('username', 'email', 'password1', 'password2', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != 'role' and not field.widget.attrs.get('class'):
                field.widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        user       = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role  = self.cleaned_data['role']
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model   = User
        fields  = ('avatar', 'bio')
        widgets = {
            'bio':    forms.Textarea(attrs={**BS, 'rows': 3}),
            'avatar': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class GameForm(forms.ModelForm):
    class Meta:
        model   = Game
        fields  = ('title', 'description', 'price', 'cover',
                   'developer', 'genre', 'release_date', 'file')
        widgets = {
            'title':        forms.TextInput(attrs=BS),
            'description':  forms.Textarea(attrs={**BS, 'rows': 4}),
            'price':        forms.NumberInput(attrs=BS),
            'cover':        forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'developer':    forms.TextInput(attrs=BS),
            'genre':        forms.Select(attrs=BS_SELECT),
            'release_date': forms.DateInput(attrs={**BS, 'type': 'date'}),
            'file':         forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model   = Review
        fields  = ('score', 'text')
        widgets = {
            'score': forms.Select(attrs=BS_SELECT),
            'text':  forms.Textarea(attrs={**BS, 'rows': 3,
                                           'placeholder': 'Напишите отзыв...'}),
        }


class ScreenshotForm(forms.ModelForm):
    class Meta:
        model   = Screenshot
        fields  = ('image', 'caption')
        widgets = {
            'image':   forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'caption': forms.TextInput(attrs={**BS,
                           'placeholder': 'Подпись (необязательно)'}),
        }


class AchievementForm(forms.ModelForm):
    class Meta:
        model   = Achievement
        fields  = ('name', 'description', 'trigger', 'points', 'icon')
        widgets = {
            'name':        forms.TextInput(attrs=BS),
            'description': forms.Textarea(attrs={**BS, 'rows': 2}),
            'trigger':     forms.Select(attrs=BS_SELECT),
            'points':      forms.NumberInput(attrs=BS),
            'icon':        forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
