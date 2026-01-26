from django.urls import path
from .views import (
    student_queries,
    create_query,
    query_detail,
    ta_queries,
    update_query_status
)

urlpatterns = [
    path('<int:course_id>/', student_queries, name='student_queries'),
    path('<int:course_id>/create/', create_query, name='create_query'),
    path('<int:course_id>/query/<int:query_id>/', query_detail, name='query_detail'),
    path('<int:course_id>/ta/', ta_queries, name='ta_queries'),
    path('<int:course_id>/query/<int:query_id>/update-status/', update_query_status, name='update_query_status'),
]
