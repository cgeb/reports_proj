from django.urls import path
from .views import (home_view, SaleListView, SaleDetailView, UploadTemplateView, csv_upload_view)

app_name = 'sales'

urlpatterns = [
  path('', home_view, name="home"),
  path('sales/', SaleListView.as_view(), name='list'),
  path('sales/upload/', csv_upload_view, name='upload'),
  path('sales/from_file/', UploadTemplateView.as_view(), name='from-file'),
  path('sales/<pk>/', SaleDetailView.as_view(), name='detail'),
]