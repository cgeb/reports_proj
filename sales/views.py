from django import forms
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.generic import ListView, DetailView, TemplateView
from pandas.core.reshape.merge import merge
from .models import Sale, Position, CSV
from products.models import Product
from customers.models import Customer
from profiles.models import Profile
from .forms import SalesSearchForm
from reports.forms import ReportForm
import pandas as pd
from .utils import get_customer_from_id, get_salesman_from_id, get_chart
import csv
from django.utils.dateparse import parse_date

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

# Create your views here.

@login_required
def home_view(request):
  sales_df = None
  positions_df = None
  merged_df = None
  df = None
  chart = None
  search_form = SalesSearchForm(request.POST or None)
  report_form = ReportForm()

  if request.method == "POST":
    date_from = request.POST.get("date_from")
    date_to = request.POST.get("date_to")
    chart_type = request.POST.get("chart_type")
    results_by = request.POST.get("results_by")

    sale_qs = Sale.objects.filter(created__date__gte=date_from, created__date__lte=date_to)
    if len(sale_qs) > 0:
      sales_df = pd.DataFrame(sale_qs.values())
      sales_df["customer_id"] = sales_df["customer_id"].apply(get_customer_from_id)
      sales_df["salesman_id"] = sales_df["salesman_id"].apply(get_salesman_from_id)
      sales_df["created"] = sales_df["created"].apply(lambda x: x.strftime("%Y-%m-%d"))
      sales_df["updated"] = sales_df["updated"].apply(lambda x: x.strftime("%Y-%m-%d"))
      sales_df.rename({"id": "sales_id", "customer_id": "customer", "salesman_id": "salesman"}, axis=1, inplace=True)

      positions_data = [
        {
          "position_id": pos.id,
          "product": pos.product.name,
          "quantity": pos.quantity,
          "price": pos.price,
          "sales_id": pos.get_sales_id()
        } for sale in sale_qs for pos in sale.get_positions()
      ]
      positions_df = pd.DataFrame(positions_data)

      merged_df = pd.merge(sales_df, positions_df, on="sales_id")
      chart = get_chart(chart_type, sales_df, results_by)
      sales_df = sales_df.to_html()
      merged_df = merged_df.to_html()

  context = {'search_form': search_form, 'report_form': report_form, 'sales_df': sales_df, 'merged_df': merged_df, "chart": chart}
  return render(request, 'sales/home.html', context)

@login_required
def csv_upload_view(request):
  if request.method == "POST":
    csv_file = request.FILES.get("file")
    csv_file_name = csv_file.name
    obj, created = CSV.objects.get_or_create(file_name=csv_file_name)

    if created:
      obj.csv_file = csv_file
      obj.save()
      with open(obj.csv_file.path, "r") as f:
        reader = csv.reader(f)
        reader.__next__()
        for row in reader:
          transaction_id = row[1]
          product = row[2]
          quantity = int(row[3])
          customer = row[4]
          date = parse_date(row[5])

          try:
            product_obj = Product.objects.get(name__iexact=product)
          except Product.DoesNotExist:
            continue

          customer_obj, _ = Customer.objects.get_or_create(name=customer)
          salesman_obj = Profile.objects.get(user=request.user)
          position_obj = Position.objects.create(product=product_obj, quantity=quantity, created=date)

          sale_obj, _ = Sale.objects.get_or_create(transaction_id=transaction_id, customer=customer_obj, salesman=salesman_obj, created=date)
          sale_obj.positions.add(position_obj)
          sale_obj.save()
      return JsonResponse({'ex': False})
    else:
      return JsonResponse({'ex': True})

class SaleListView(LoginRequiredMixin, ListView):
  model = Sale
  template_name = 'sales/main.html'

class SaleDetailView(LoginRequiredMixin, DetailView):
  model = Sale
  template_name = 'sales/detail.html'

class UploadTemplateView(LoginRequiredMixin, TemplateView):
  template_name = 'sales/from_file.html'