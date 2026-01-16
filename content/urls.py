from django.urls import path
from .views import delete_material, toggle_visibility

urlpatterns = [
    path('delete/<int:material_id>/', delete_material),
    path('toggle/<int:material_id>/', toggle_visibility),
]
