"""
URL configuration for XChicks project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, include 
from ChicksApp.views import * 
from ChicksApp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.indexpage, name='index'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.Login, name='Login'),
    path('logout/', views.Logout, name='Logout'),

    #for the managers dashboard
    path('managersdashboard/', views.Managersdashboard, name='Managersdashboard'),
    path('chickrequests/', views.ViewChickRequests, name='Viewchickrequests'),
    path('feedrequests/', views.ViewFeedRequests, name='Viewfeedrequests'),
    path('farmerreview/', views.FarmerReview, name='Farmerreview'),
    path('farmerrecords/', views.FarmerRecords, name='Farmerrecords'),
    path('chickstock/', views.chickStock, name='Chickstock'),
    path('feedstock/', views.feedStock, name='Feedstock'),
    path('updatechickstock/', views.UpdateChickStock, name='Updatechickstock'),
    path('updatefeedstock/', views.UpdateFeedStock, name='Updatefeedstock'),
    path('reports/', views.Reports, name='Reports'),
    path('sales/', views.Sales, name='Sales'),

    #sales agent dashboard
    path('salesagentdashboard/', views.SalesAgentdashboard, name='salesagentdashboard'),
    path('addchickrequest/', views.AddChickRequest, name='addchickrequest'),
    path('addfeedrequest/', views.AddFeedRequest, name='addfeedrequest'),
    path('registerfarmer/', views.RegisterFarmer, name='registerfarmer'),
    path('salesagentchickrequests/', views.ViewSalesAgentChickRequests, name='salesagentchickrequests'),
    path('salesagentfeedrequests/', views.ViewSalesAgentFeedRequests, name='salesagentfeedrequests'),
]
