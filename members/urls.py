from django.urls import path
from . import views

urlpatterns = [
    path('', views.member_list, name='member_list'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('export_excel/', views.export_excel, name='export_excel'),
    path('import_excel/', views.import_excel, name='import_excel'),
    path('generate_invoice_pdf/<int:member_id>/', views.generate_invoice_pdf, name='generate_invoice_pdf'),
]
