from django.urls import path, include
from . import views

app_name = 'teams'
urlpatterns = [
    path('', views.home, name='home'),
    path('get_team/', views.get_team, name='get-team'),
    path('create-team/', views.createTeam, name='create-team'),
    path('join-team/', views.joinTeam, name='join-team'),
    path('accept-team-mate/', views.acceptTeamMateView, name='accept-teammate'),
    path('complete-profile/', views.profileCompleteView, name='complete-profile'),
    path('scoreboard/', views.scoreboardView, name='scoreboard'),
    path('rules/', views.rules, name='rules'),
    path('playerdetail/', views.playerdetail, name='teamdetail'),
    path('detailedscore/',views.detailedScoreboardView, name='detailedscore'),
    path('chase/', views.get_level, name='get-level'),
    path('chase/1/', views.start_hunt, name='start_hunt'),
    path('logout/', views.logout_view, name='logout'),
    path('root/', views.root_view, name='root'),
]
