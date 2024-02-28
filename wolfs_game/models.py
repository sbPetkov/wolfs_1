from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class Room(models.Model):
    admin = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='administered_rooms')
    users = models.ManyToManyField(User, related_name='joined_rooms')


class Character(models.Model):
    role = models.CharField(max_length=50)
    is_role_good = models.BooleanField(default=True)

    def __str__(self):
        return self.role


class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.DO_NOTHING)
    player_character = models.ForeignKey(Character, on_delete=models.DO_NOTHING)
    is_alive = models.BooleanField(default=True)
    room = models.ForeignKey(Room, on_delete=models.DO_NOTHING)

    def __str__(self):
        return f'{self.user.first_name} - {self.player_character.role}'


class Game(models.Model):
    all_players = models.ManyToManyField(Player, related_name='all_games', default=None, blank=True)
    good_players = models.ManyToManyField(Player, related_name='good_games', default=None, blank=True)
    wolfs = models.ManyToManyField(Player, related_name='wolf_games', default=None, blank=True)
    wolf_votes = models.ManyToManyField(Player, related_name='wolf_votes_games', default=None, blank=True)
    healer_vote = models.ManyToManyField(Player, related_name='healer_vote_games', default=None, blank=True)
    is_next_round_active = models.BooleanField(default=True)






