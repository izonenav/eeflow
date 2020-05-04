"""eeflow URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from erp.views import voucher_list, nacct_list, payment_list, invoice_list, receipt_list

urlpatterns = [
    path('voucher_list/', voucher_list, name='voucher_list'),  # 채무발생
    path('payment_list/', payment_list, name='payment_list'),  # 채무정리
    path('invoice_list/', invoice_list, name='invoice_list'),  # 채권발생
    path('receipt_list/', receipt_list, name='receipt_list'),  # 채권정리
    path('nacct_list/', nacct_list, name='nacct_list'),  # 일반전표
]
