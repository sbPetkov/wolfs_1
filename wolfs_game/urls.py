from django.urls import path

from wolfs_game.views import IndexView, RoomCreateView, RoomDetailsView, CreateUserView, CustomLoginView, \
    CustomLogoutView, CreateGameView, game, reveal_results, hang_player, night_phase_selector, DeleteRoomView, \
    DeleteGameView

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('new_room/', RoomCreateView.as_view(), name='create-room'),
    path('room_details/<int:pk>', RoomDetailsView.as_view(), name='details-room'),
    path('create_user/', CreateUserView.as_view(), name='create-user'),
    path('login_user/', CustomLoginView.as_view(), name='login-user'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('create_game/<int:pk>/', CreateGameView.as_view(), name='create-game'),
    path('game/<int:pk>', game, name='game'),
    path('night_phase/<int:pk>', night_phase_selector, name='night-phase'),
    path('reveal_results/<int:pk>', reveal_results, name='submit-results'),
    path('hang_player/<int:pk>', hang_player, name='hang-or-go'),
    path('delete_room/<int:pk>', DeleteRoomView.as_view(), name='delete-room'),
    path('delete_game/<int:pk>', DeleteGameView.as_view(), name='delete-game'),

]