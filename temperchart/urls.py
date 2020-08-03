from django.urls import path
from temperchart.views import ChartData, CurrentChartData

urlpatterns = [
    path('get_chart_data/', ChartData.as_view(), name='get_chart_data'),
    path('get_current_chart_data/', CurrentChartData.as_view(), name='get_current_chart_data'),
]
