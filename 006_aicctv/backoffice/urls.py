from django.urls import path
from . import views

urlpatterns = [
    path('',                          views.login_view,      name='bo_login'),
    path('logout/',                   views.logout_view,     name='bo_logout'),
    path('dashboard/',                views.dashboard,       name='bo_dashboard'),
    path('profile/',                  views.profile,         name='bo_profile'),
    path('employee/',                 views.employee_list,   name='bo_employee_list'),
    path('employee/create/',          views.employee_create, name='bo_employee_create'),
    path('employee/<int:pk>/edit/',   views.employee_edit,   name='bo_employee_edit'),
    path('employee/<int:pk>/delete/', views.employee_delete, name='bo_employee_delete'),
    path('retrain/',                  views.retrain_view,    name='bo_retrain'),
]
