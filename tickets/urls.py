from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DashboardView, TicketViewSet

router = DefaultRouter()
router.register(r'tickets', TicketViewSet, basename='ticket')

urlpatterns = [
    # Dashboard Frontend Page
    path('', DashboardView.as_view(), name='dashboard'),
    
    # API endpoints
    path('api/', include(router.urls)),
]
