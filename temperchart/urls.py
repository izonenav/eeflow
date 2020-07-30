from django.urls import path
from temperchart.views import get_chart_data

urlpatterns = [
    path('get_chart_data/', get_chart_data, name='get_chart_data'),
]
