from django.contrib import admin
from .models import Room, Character, Player, Game

# Register your models here.
admin.site.register(Room)
admin.site.register(Character)
admin.site.register(Player)
admin.site.register(Game)
