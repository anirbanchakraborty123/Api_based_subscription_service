from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SubscriptionViewSet, PlanViewSet

router = DefaultRouter()
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'plans', PlanViewSet, basename='plan')

urlpatterns = [
    path('api/v1/', include(router.urls)),
]