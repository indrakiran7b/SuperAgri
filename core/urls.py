# # core/urls.py
# from django.urls import path
# from . import views

# app_name = 'core'  # Add namespace to avoid URL conflicts

# urlpatterns = [
#     path('', views.farm_details, name='farm_details'),
#     path('crop-recommendation/', views.crop_recommendation, name='crop_recommendation'),
#     path('crop-plan/', views.crop_plan, name='crop_plan'),
#     path('plan/<int:plan_id>/', views.plan_detail, name='plan_detail'),
#     path('monitoring/', views.monitoring_dashboard, name='monitoring_dashboard'),
#     path('task/<int:task_id>/complete/', views.complete_task, name='complete_task'),
#     path('plan/<int:plan_id>/pesticides/', views.generate_pesticide_recommendations, name='generate_pesticide_recommendations'),
#     path('recommendations/', views.view_recommendations, name='view_recommendations'),
#     path('recommendations/generate/', views.generate_recommendations, name='generate_recommendations'),
# ]

# core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.farm_details, name='farm_details'),
    path('farm-details/', views.farm_details, name='farm_details'),
    path('crop-plan/', views.crop_plan, name='crop_plan'),
    path('plan/<int:plan_id>/', views.plan_detail, name='plan_detail'),
    path('recommendations/', views.view_recommendations, name='view_recommendations'),
    path('recommendations/generate/', views.generate_recommendations, name='generate_recommendations'),
    path('plan/<int:plan_id>/pesticides/', views.generate_pesticide_recommendations, name='generate_pesticide_recommendations'),
    path('monitoring/', views.monitoring_dashboard, name='monitoring_dashboard'),
    path('task/<int:task_id>/complete/', views.complete_task, name='complete_task'),
]