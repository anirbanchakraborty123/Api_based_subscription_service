import logging
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Prefetch
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django_ratelimit.decorators import ratelimit
from django.db import models

from .models import Subscription, Feature, Plan
from .serializers import (
    SubscriptionCreateSerializer,
    SubscriptionUpdateSerializer,
    SubscriptionListSerializer,
    PlanSerializer,
)


logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination class for all viewsets."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user subscriptions.

    Provides CRUD operations for subscriptions with optimized queries
    and proper caching.
    """

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "create":
            return SubscriptionCreateSerializer
        elif self.action in ["update", "partial_update", "change_plan"]:
            return SubscriptionUpdateSerializer
        return SubscriptionListSerializer

    def get_queryset(self):
        """
        Get optimized queryset for subscriptions.
        Uses select_related and prefetch_related to avoid N+1 queries.
        """
        return (
            Subscription.objects.select_related("user", "plan")
            .prefetch_related(
                Prefetch(
                    "plan__features",
                    queryset=Feature.objects.filter(is_active=True).order_by("name"),
                )
            )
            .filter(user=self.request.user)
            .order_by("-start_date")
        )

    @method_decorator(ratelimit(key="user", rate="10/min", method="POST"))
    def create(self, request, *args, **kwargs):
        """Create a new subscription with rate limiting."""
        logger.info(f"Creating subscription for user {request.user.username}")
        return super().create(request, *args, **kwargs)

    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    @method_decorator(vary_on_headers("Authorization"))
    def list(self, request, *args, **kwargs):
        """List user's subscriptions with caching."""
        cache_key = f"user_subscriptions_{request.user.id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            logger.info(
                f"Serving cached subscriptions for user {request.user.username}"
            )
            return Response(cached_data)

        response = super().list(request, *args, **kwargs)
        if response.status_code == 200:
            cache.set(cache_key, response.data, timeout=60 * 5)  # Cache for 5 minutes

        return response

    @method_decorator(ratelimit(key="user", rate="5/min", method="PUT"))
    @action(detail=True, methods=["put"], url_path="change-plan")
    def change_plan(self, request, pk=None):
        """Change subscription plan with rate limiting."""
        subscription = self.get_object()
        serializer = SubscriptionUpdateSerializer(
            subscription, data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            response_serializer = SubscriptionListSerializer(
                subscription, context={"request": request}
            )
            logger.info(f"Plan changed for subscription {pk}")
            return Response(response_serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @method_decorator(ratelimit(key="user", rate="10/min", method="POST"))
    @action(detail=True, methods=["post"], url_path="deactivate")
    def deactivate(self, request, pk=None):
        """Deactivate a subscription."""
        subscription = self.get_object()

        if not subscription.is_active:
            return Response(
                {"error": "Subscription is already inactive"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subscription.deactivate()
        serializer = SubscriptionListSerializer(
            subscription, context={"request": request}
        )

        logger.info(f"Deactivated subscription {pk}")
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="active")
    def active_subscription(self, request):
        """Get user's currently active subscription."""
        cache_key = f"active_subscription_{request.user.id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        try:
            subscription = self.get_queryset().get(is_active=True)
            serializer = SubscriptionListSerializer(
                subscription, context={"request": request}
            )
            cache.set(
                cache_key, serializer.data, timeout=60 * 10
            )  # Cache for 10 minutes
            return Response(serializer.data)
        except Subscription.DoesNotExist:
            return Response(
                {"message": "No active subscription found"},
                status=status.HTTP_404_NOT_FOUND,
            )


class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for plans."""

    queryset = Plan.objects.filter(is_active=True).prefetch_related("features")
    serializer_class = PlanSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    @method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
    def list(self, request, *args, **kwargs):
        """List available plans with caching."""
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
    def retrieve(self, request, *args, **kwargs):
        """Retrieve plan details with caching."""
        return super().retrieve(request, *args, **kwargs)
