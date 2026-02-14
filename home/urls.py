from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('nearby_hospitals/', views.nearby_hospitals, name='nearby_hospitals'),
    path("get_route/", views.get_route, name="get_route")
]