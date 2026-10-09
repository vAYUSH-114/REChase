import datetime
import json

from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import make_aware


class Team(models.Model):
    name = models.CharField(max_length=128, null=True, unique=True)
    code = models.CharField(max_length=128, null=True, blank=True)
    member_count = models.IntegerField(default=0, null=True)
    current_level = models.IntegerField(default=0, null=True)
    current_question = models.IntegerField(default=-1, null=True)
    question = models.CharField(max_length=255, null=True, blank=True, default='-1')
    answers = models.CharField(max_length=8192, null=True, blank=True, default='{}')
    score = models.IntegerField(default=0, null=True)
    rank = models.IntegerField(default=0, null=True)
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def answerCorr(self, curr_lvl=1, answer=None):
        self.current_level = curr_lvl + 1
        self.current_question = -1
        self.question = '-1'
        self.score = self.score + 10
        if curr_lvl == 1:
            temp = {}
        else:
            temp = json.loads(self.answers)
        temp[curr_lvl] = answer
        self.answers = json.dumps(temp)
        self.timestamp = make_aware(datetime.datetime.now())
        self.save()

    

    def specialCipher(self, answer):
        temp = json.loads(self.answers)

        if self.current_question == 1:
            temp[str(self.current_level)] = {}
        temp[str(self.current_level)][str(self.current_question)] = answer

        self.answers = json.dumps(temp)
        if self.current_question == 7:
            self.current_level = self.current_level + 1
            self.current_question = -1
            self.question = '-1'
            self.score = self.score + 10
            self.timestamp = make_aware(datetime.datetime.now())

        else:
            self.current_question = self.current_question + 1

        self.save()




class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=128, null=True)
    roll_no = models.CharField(max_length=128, null=True, blank=True)
    email = models.EmailField(max_length=254, null=True, blank=True)
    phone = models.CharField(max_length=13, null=True)
    gender = models.CharField(max_length=2,
                              choices=(
                                  ('M', 'Male'),
                                  ('F', 'Female'),
                                  ('O', 'Others'),
                              ),
                              default='M')
    college = models.CharField(max_length=128, default='NIT Durgapur')
    team_code = models.CharField(max_length=128, null=True, blank=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    accepted = models.SmallIntegerField(default=0)

    def __str__(self):
        return self.name or self.email or self.user.username

class Teammate(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='teammates')
    name = models.CharField(max_length=128)
    roll_no = models.CharField(max_length=128)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
