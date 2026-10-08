from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout
from . import models
import datetime
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from .decorators import team_required
from .forms import (
    TeamCreationForm,
    ProfileFillForm,
)
from .utils import makeCode
from django.conf import settings

def save_profile(backend, user, response, *args, **kwargs):
    if backend.name == 'google-oauth2':
        player, created = models.Player.objects.get_or_create(user=user)
        player.timestamp = datetime.datetime.now()
        email = response.get('email') or getattr(user, 'email', None)
        if email:
            player.email = email
        name = response.get('name')
        if not name:
            given = response.get('given_name', '')
            family = response.get('family_name', '')
            name = (f"{given} {family}").strip()
        if name:
            player.name = name
        player.save()


def home(request):
    user = request.user
    if not user.is_authenticated:
        # For managing event Wait and Finish
        print("User is not authenticated")
        context = {}
        if datetime.datetime.now() < settings.START_TIME:
            context = {'wait': 1, 'cur_time': datetime.datetime.now(),
                       'start_time': settings.START_TIME}
        elif datetime.datetime.now() > settings.END_TIME:
            context['finish'] = 1
        else:
            context['started'] = 1
        return render(request, 'teams/base_menu.html', context)

    profile = models.Player.objects.get(user=user)
    if profile.phone is None:
        return redirect('teams:complete-profile')
    if profile.team is None or profile.accepted == 0:
        return render(request, 'teams/no_team.html', {})
    team = models.Team.objects.get(id=profile.team.pk)
    everyone = models.Player.objects.filter(team=team.pk)
    team_players = everyone.filter(accepted=1)
    context = {'team': team, 'profile': profile, 'players': team_players, 'max_level': settings.FINAL_LEVEL}
    if team.member_count < 5:
        applicants = everyone.filter(accepted=0)
        context['applicants'] = applicants

    # For managing event Wait and Finish  
    if datetime.datetime.now() < settings.START_TIME:
        context['wait'] = 1
        context['cur_time'] = datetime.datetime.now()
        context['start_time'] = settings.START_TIME
    elif datetime.datetime.now() > settings.END_TIME:
        context['finish'] = 1
    else:
        context['started'] = 1

    return render(request, 'teams/teamHome.html', context)

@login_required
@team_required
def get_level(request):
    user = request.user
    profile = models.Player.objects.get(user=user)

    team = models.Team.objects.get(id=profile.team.pk)
    level = team.current_level
    if level > settings.FINAL_LEVEL:
        return redirect('teams:scoreboard')

    return redirect(request.path + str(1))

@login_required
@team_required
def start_hunt(request):
    context = {'cur_time': datetime.datetime.now(), 'start_time': settings.START_TIME}
    return render(request, 'teams/start_location.html', context)



@login_required
def get_team(request):
    return render(request, 'teams/no_team.html', {})


@login_required
def createTeam(request):
    context = {}
    user = request.user
    profile = models.Player.objects.get(user=user)
    if profile.phone is None:
        return redirect('teams:complete-profile')
    form = TeamCreationForm(request.POST or None)
    if form.is_valid():
        obj = form.save(commit=False)
        code = makeCode()
        obj.code = code
        obj.member_count = 1
        obj.save()
        curr_user = models.Player.objects.get(user=user)
        curr_user.team = obj
        curr_user.team_code = code
        curr_user.accepted = 1
        curr_user.save()
        return redirect('teams:home')

    context['form'] = form
    return render(request, 'teams/teamCreation.html', context=context)


@login_required
def joinTeam(request):
    context = {}
    user = request.user
    profile = models.Player.objects.get(user=user)
    if profile.phone is None:
        return redirect('teams:complete-profile')
    if profile.accepted == 1 and profile.team is not None:
        return redirect('teams:home')
    if request.method == 'POST':
        code = request.POST.get('code', -1)
        team = models.Team.objects.filter(code=code).first()
        if not team:
            context['wrong_code'] = 'Invalid code entered.'
            return render(request, 'teams/teamJoin.html', context=context)
        if team.member_count >= 5:
            context['team_full'] = 'Team is full.'
            return render(request, 'teams/teamJoin.html', context=context)
        profile.team = team
        profile.team_code = team.code
        profile.accepted = 0
        profile.save()
        context['sent'] = 1
        return render(request, 'teams/no_team.html', context=context)

    return render(request, 'teams/teamJoin.html', context=context)


@login_required
def profileCompleteView(request):
    context = {}
    user = request.user
    profile, _ = models.Player.objects.get_or_create(user=user)
    form = ProfileFillForm(request.POST or None)
    if form.is_valid():
        form.clean()
        profile.name = form.cleaned_data['name']
        profile.phone = form.cleaned_data['phone']
        profile.gender = form.cleaned_data['gender']
        profile.college = form.cleaned_data['college']
        profile.save()
        return redirect('teams:home')
    context['form'] = form
    return render(request, 'teams/createProfile.html', context)


@login_required
@team_required
def leaveTeamView(request):  # needs to be removed
    context = {}
    user = request.user
    profile = models.Player.objects.get(user=user)
    team = models.Team.objects.get(id=profile.team.pk)
    if request.method == 'POST':
        if team.member_count == 1:
            team.delete()
        else:
            team.member_count = team.member_count - 1
            team.save()
        profile.team = None
        profile.team_code = None
        profile.save()
        return redirect('teams:get-team')
    context['team'] = team
    context['profile'] = profile
    return render(request, 'teams/confirmLeave.html', context)


@login_required
def acceptTeamMateView(request):
    user = request.user
    if not user.is_authenticated:
        return redirect('/oauth/login/google-oauth2/')

    profile = models.Player.objects.get(user=user)
    if profile.phone is None:
        return redirect(reverse_lazy('teams:complete-profile'))

    if profile.accepted == 0 or profile.team is None:
        return redirect(reverse_lazy('teams:get-team'))

    context = {}
    owner = models.Player.objects.get(user=request.user)
    team = models.Team.objects.get(pk=owner.team.id)
    applicantId = int(request.POST.get('ID'))
    verdict = request.POST.get('verdict')
    applicant = models.Player.objects.get(id=applicantId)
    if verdict == 'Reject':
        applicant.team = None
        applicant.save()
    elif verdict == 'Accept':
        if team.member_count >= 5:
            context['team_full'] = 'Team is full.'
            return redirect('teams:home')
        applicant.accepted = 1
        applicant.team_code = team.code
        applicant.save()
        team.member_count = team.member_count + 1
        team.save()
    return redirect('teams:home')


def scoreboardView(request):
    context = {'cur_time': datetime.datetime.now(), 'start_time': settings.START_TIME}

    cur_rank = 0
    try:
        all_teams = models.Team.objects.all()
        qs = all_teams.order_by('-score', 'timestamp')
        for pl in qs:
            pl.rank = cur_rank
        context['qs'] = qs
    except:
        context['wrong'] = 1
    if datetime.datetime.now() < settings.START_TIME:
        context['wait'] = 1
    return render(request, 'teams/leaderBoard.html', context)


def rules(request):
    context = {}
    return render(request, 'teams/rules.html', context)


def playerdetail(request):
    if not request.user.is_authenticated:
        return redirect(reverse_lazy("teams:home"))
    if not request.user.is_superuser:
        return redirect(reverse_lazy("teams:home"))
    all_players = models.Player.objects.all().order_by('-team_code', 'timestamp')
    context = {'players': all_players}
    return render(request, 'teams/playerdetail.html', context)

def detailedScoreboardView(request):
    if not request.user.is_authenticated:
        return redirect(reverse_lazy("teams:home"))
    if not request.user.is_superuser:
        return redirect(reverse_lazy("teams:home"))
    
    context = {'cur_time': datetime.datetime.now(), 'start_time': settings.START_TIME}

    cur_rank = 0
    
    all_teams = models.Team.objects.all()
    qs = all_teams.order_by('-score', 'timestamp')
    allplayers = models.Player.objects.all()
    qp = []
    for pl in qs:
        pl.rank = cur_rank
        tc = pl.code
        sz = pl.member_count
        players = []
        for eachplayer in allplayers:
            teamcode = eachplayer.team_code
            if teamcode == tc:
                players.append({
                    "name" : eachplayer.name,
                    "email" : eachplayer.email,
                })
        cnt_player = 1 
        player1 = "-"
        player2 = "-"
        email1 = "-"
        email2 = "-"
        for xx in players:
            if cnt_player==1:
                player1 = xx["name"]
                email1 = xx["email"]
            if cnt_player==2:
                player2 = xx["name"]
                email2 = xx["email"]
            cnt_player+=1
        
        qp.append(
            {
                "rank" : cur_rank,
                "name" : pl.name,
                "score" : pl.score,
                "ques" : pl.current_level,
                "player1" : player1,
                "player2" : player2,
                "email1" : email1,
                "email2" : email2
            }
        )
        # cur_rank += 1
        context['qp'] = qp
        leveldetail=[]
        for i in range(1,13):
            curr_level = i
            teams = all_teams.filter(current_level=curr_level)
            num = len(teams)
            leveldetail.append(
                {
                    "level" : curr_level,
                    "num" : num
                }
            )
        context['leveldetail'] = leveldetail
    return render(request, 'teams/detailed_leaderBoard.html', context)


def logout_view(request):
    auth_logout(request)
    return redirect('teams:home')


def root_view(request):
    context = {}
    if request.method == 'POST':
        passkey = request.POST.get('passkey', '').strip()
        if passkey.lower() == 'override':
            context['success'] = True
        else:
            context['error'] = 'You have entered a wrong passkey. Try again and decode again!!'
            context['entered_passkey'] = passkey
    return render(request, 'teams/root.html', context)
