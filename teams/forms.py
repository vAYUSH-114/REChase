from django import forms

from .models import (
    Team,
    Player,
    Teammate
)

class TeamCreationForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name']


class ProfileFillForm(forms.ModelForm):
    team_name = forms.CharField(max_length=128, required=True)
    phone = forms.CharField(max_length=13, min_length=10)

    class Meta:
        model = Player
        fields = ['name', 'roll_no', 'phone', 'gender', 'college']

class TeammateForm(forms.ModelForm):
    class Meta:
        model = Teammate
        fields = ['name', 'roll_no']
