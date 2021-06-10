from typing import List
from django.contrib.auth import login
from django.shortcuts import render, get_object_or_404
from profiles.models import Profile
from django.http import JsonResponse
from .utils import get_report_image
from .models import Report
from .forms import ReportForm
from django.views.generic import ListView, DetailView

from django.conf import settings
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

# Create your views here.

class ReportListView(LoginRequiredMixin, ListView):
  model = Report
  template_name = "reports/main.html"

class ReportDetailView(LoginRequiredMixin, DetailView):
  model = Report
  template_name = "reports/detail.html"

@login_required
def create_report_view(request):
  if request.is_ajax():
    form = ReportForm(request.POST or None)
    if form.is_valid():
      instance = form.save(commit=False)
      image = request.POST.get("image")
      decoded_img = get_report_image(image)
      instance.image = decoded_img
      instance.author = Profile.objects.get(user=request.user)
      instance.save()
      return JsonResponse({'msg': 'success'})
    return JsonResponse({'error': 'Something went wrong'})

def render_pdf_view(_, pk):
    template_path = 'reports/pdf.html'
    obj = get_object_or_404(Report, pk=pk)
    context = {'obj': obj}

    response = HttpResponse(content_type='application/pdf')

    response['Content-Disposition'] = 'filename="report.pdf"'

    template = get_template(template_path)
    html = template.render(context)

    pisa_status = pisa.CreatePDF(
       html, dest=response)

    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response