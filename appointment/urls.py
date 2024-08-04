from django.urls import path
from . import views

urlpatterns = [
    path('add/', views.AppointmentView.as_view(), name='appointment'),
    path('view/', views.appointment_list, name='view_appointments'),
]