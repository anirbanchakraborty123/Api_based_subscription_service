from rest_framework import serializers
from django.contrib.auth.models import User
from django.db import transaction
from django.core.cache import cache
import logging
from .models import Feature, Plan, Subscription
from django.utils import timezone

logger = logging.getLogger(__name__)


class FeatureSerializer(serializers.ModelSerializer):
    """Serializer for Feature model."""

    class Meta:
        model = Feature
        fields = ["id", "name", "description", "is_active"]
        read_only_fields = ["id"]

    def validate_name(self, value):
        """Validate feature name is not empty and unique."""
        if not value.strip():
            raise serializers.ValidationError("Feature name cannot be empty")

        # Check uniqueness during update
        if self.instance and self.instance.name != value:
            if Feature.objects.filter(name=value).exists():
                raise serializers.ValidationError(
                    "Feature with this name already exists"
                )

        return value.strip()


class PlanSerializer(serializers.ModelSerializer):
    """Serializer for Plan model with nested features."""

    features = FeatureSerializer(many=True, read_only=True)
    feature_count = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = [
            "id",
            "name",
            "description",
            "price",
            "features",
            "feature_count",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_feature_count(self, obj):
        """Get count of active features in the plan."""
        return obj.features.filter(is_active=True).count()

    def validate_price(self, value):
        """Validate price is not negative."""
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative")
        return value

    def validate_name(self, value):
        """Validate plan name."""
        if not value.strip():
            raise serializers.ValidationError("Plan name cannot be empty")
        return value.strip()


class SubscriptionListSerializer(serializers.ModelSerializer):
    """Serializer for listing subscriptions with nested plan and feature data."""

    plan = PlanSerializer(read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    duration_days = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = [
            "id",
            "user_email",
            "plan",
            "start_date",
            "end_date",
            "is_active",
            "duration_days",
            "created_at",
        ]
        read_only_fields = ["id", "start_date", "created_at"]

    def get_duration_days(self, obj):
        """Calculate subscription duration in days."""
        if obj.end_date:
            return (obj.end_date - obj.start_date).days
        return (timezone.now() - obj.start_date).days


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new subscriptions."""

    class Meta:
        model = Subscription
        fields = ["plan"]

    def validate_plan(self, value):
        """Validate plan is active."""
        if not value.is_active:
            raise serializers.ValidationError("Cannot subscribe to inactive plan")
        return value

    @transaction.atomic
    def create(self, validated_data):
        """Create new subscription, deactivating any existing active subscription."""
        user = self.context["request"].user
        plan = validated_data["plan"]

        # Deactivate existing active subscription
        existing_subscription = Subscription.objects.filter(
            user=user, is_active=True
        ).first()

        if existing_subscription:
            existing_subscription.deactivate()
            logger.info(f"Deactivated existing subscription {existing_subscription.id}")

        # Create new subscription
        subscription = Subscription.objects.create(user=user, **validated_data)
        logger.info(
            f"Created new subscription {subscription.id} for user {user.username}"
        )

        # Clear user's subscription cache
        cache.delete(f"user_subscriptions_{user.id}")

        return subscription


class SubscriptionUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating subscription plan."""

    class Meta:
        model = Subscription
        fields = ["plan"]

    def validate_plan(self, value):
        """Validate plan is active and different from current."""
        if not value.is_active:
            raise serializers.ValidationError("Cannot switch to inactive plan")

        if self.instance and self.instance.plan == value:
            raise serializers.ValidationError("Already subscribed to this plan")

        return value

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update subscription plan."""
        old_plan = instance.plan.name
        instance.plan = validated_data["plan"]
        instance.save(update_fields=["plan", "updated_at"])

        logger.info(
            f"Updated subscription {instance.id} from {old_plan} to {instance.plan.name}"
        )

        # Clear user's subscription cache
        cache.delete(f"user_subscriptions_{instance.user.id}")

        return instance
