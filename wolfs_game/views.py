from random import shuffle

from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, ListView, DetailView, DeleteView
from collections import Counter
from django.shortcuts import get_object_or_404

from wolfs_game.forms import CustomUserCreationForm
from wolfs_game.models import Room, Character, Player, Game


class IndexView(ListView):
    model = Room
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['games'] = Game.objects.all()
        return context


class RoomCreateView(CreateView):
    model = Room
    fields = ['admin', 'users']
    template_name = 'create_room.html'

    def get_success_url(self):
        return reverse('index')


class RoomDetailsView(DetailView):
    model = Room
    template_name = 'room_details.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        characters = list(Character.objects.all())
        shuffle(characters)
        context['characters'] = characters

        users = list(self.object.users.all())
        shuffle(users)
        context['users'] = users
        return context

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()  # Ensure object is available
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        room = self.object
        for user_id, character_id in request.POST.items():
            if user_id != 'csrfmiddlewaretoken':  # Skip CSRF token
                user = room.users.get(id=user_id)
                character = Character.objects.get(id=character_id)
                player, created = Player.objects.get_or_create(user=user, defaults={'player_character': character, 'room': room})
                if not created:
                    player.player_character = character
                    player.is_alive = True
                    player.room = room
                    player.save()
        return render(request, self.template_name, self.get_context_data())


class DeleteRoomView(DeleteView):
    model = Room
    template_name = 'delete_room.html'
    success_url = reverse_lazy('index')


class CreateUserView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'create_user.html'
    success_url = reverse_lazy('index')


class CustomLoginView(LoginView):
    template_name = 'login.html'

    def get_success_url(self):
        return reverse('index')


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('index')


class DeleteGameView(DeleteView):
    model = Game
    template_name = 'delete_game.html'
    success_url = reverse_lazy('index')


class CreateGameView(CreateView):
    model = Game
    template_name = 'create_game.html'
    fields = []  # No fields needed as we'll populate them programmatically

    def get_success_url(self):
        # Redirect to some URL after the game is created
        return reverse('index')  # Change this to your desired URL

    def form_valid(self, form):
        room_id = self.kwargs['pk']  # Assuming you pass the room ID in the URL
        room_players = Player.objects.filter(room_id=room_id)

        # Filter players for different categories
        all_players = room_players
        good_players = room_players.filter(is_alive=True, player_character__is_role_good=True)
        wolfs = room_players.filter(is_alive=True, player_character__is_role_good=False)

        # Create the Game instance with the filtered players
        game = form.save(commit=False)
        game.save()
        game.all_players.set(all_players)
        game.good_players.set(good_players)
        game.wolfs.set(wolfs)

        # Set wolf_votes and healer_vote as empty
        game.wolf_votes.set([])
        game.healer_vote.set([])

        return super().form_valid(form)


def game(request, pk):
    current_game = get_object_or_404(Game, pk=pk)

    try:
        user_player = Player.objects.get(user=request.user)
    except Player.DoesNotExist:
        user_player = None

    context = {
        "game": current_game,
        "user_player": user_player,
    }

    return render(request, 'game.html', context)


def reveal_results(request, pk):
    current_game = get_object_or_404(Game, pk=pk)
    healed_player = current_game.healer_vote.first()
    players_voted_by_wolves = current_game.wolf_votes.all()
    vote_count = Counter(players_voted_by_wolves)
    most_common_votes = vote_count.most_common()
    if len(most_common_votes) > 1 and most_common_votes[0][1] == most_common_votes[1][1]:
        player_to_be_killed = most_common_votes[0][0]
    else:
        player_to_be_killed = most_common_votes[0][0]

    if healed_player:
        if healed_player == player_to_be_killed:
            current_game.healer_vote.clear()
            current_game.wolf_votes.clear()
        else:
            player_to_be_killed.is_alive = False
            player_to_be_killed.save()
    else:
        if player_to_be_killed:
            player_to_be_killed.is_alive = False
            player_to_be_killed.save()

    # Clear the vote lists
    current_game.healer_vote.clear()
    current_game.wolf_votes.clear()

    current_game.is_next_round_active = False
    current_game.save()

    return redirect('game', pk=pk)


def hang_player(request, pk):
    current_game = get_object_or_404(Game, pk=pk)
    players_in_game = current_game.all_players.all()

    if request.method == 'POST':
        player_id = request.POST.get('player')
        if player_id == 'NONE':
            # If 'NONE' is selected, no player is being killed
            current_game.is_next_round_active = True
        else:
            # Find the player selected to be hanged and set is_alive to False
            player = Player.objects.get(pk=player_id)
            player.is_alive = False
            player.save()

            # Set is_next_round_active to True
            current_game.is_next_round_active = True

        current_game.save()
        return redirect('game', pk=pk)

    context = {
        'current_game': current_game,
        'players_in_game': players_in_game,
    }
    return render(request, 'hanging.html', context)


def night_phase(request, pk):
    user = request.user
    current_game = get_object_or_404(Game, pk=pk)
    player = Player.objects.get(user=user)
    if not player.is_alive:
        return redirect('game', pk=pk)
    context = {
        "current_game": current_game
    }

    if player.player_character.role == "Wolf":
        if request.method == "POST":
            selected_player_id = request.POST.get('wolf_vote')
            selected_player = Player.objects.get(pk=selected_player_id)
            current_game.wolf_votes.add(selected_player)
            return redirect('game', pk=pk)
        else:
            return render(request, 'wolf.html', context)
    elif player.player_character.role == "Healer":
        if request.method == "POST":
            selected_player_id = request.POST.get('healer_vote')
            selected_player = Player.objects.get(pk=selected_player_id)
            current_game.healer_vote.add(selected_player)
            return redirect('game', pk=pk)
        else:
            players = current_game.all_players
            context['players'] = players
            return render(request, 'healer.html', context)
    elif player.player_character.role == "Prophet":
        if request.method == "POST":
            selected_player_id = request.POST.get('prophet_vote')
            selected_player = Player.objects.get(pk=selected_player_id)
            if selected_player.player_character.is_role_good:
                result = f"{selected_player.user.first_name} is good player"
            else:
                result = f"{selected_player.user.first_name} is WOLF"
            context['result'] = result
            return render(request, 'prophet_result.html', context)
        else:
            players = current_game.all_players
            context['players'] = players
            return render(request, 'prophet.html', context)
    else:
        players = current_game.all_players
        context['players'] = players
        return render(request, 'village_man.html', context)


def night_phase_selector(request, pk):
    current_game = get_object_or_404(Game, pk=pk)
    if current_game.is_next_round_active:
        return night_phase(request, pk)
    else:
        return game(request, pk)