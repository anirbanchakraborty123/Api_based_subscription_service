import logging
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


logger = logging.getLogger(__name__)


class TimestampedModel(models.Model):
    """Abstract base model with timestamp fields."""
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("Timestamp when the record was created")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("Timestamp when the record was last updated")
    )

    class Meta:
        abstract = True


class Feature(TimestampedModel):
    """
    Model representing a feature that can be included in subscription plans.
    
    Features are the individual capabilities or services that users get
    access to through their subscription plans.
    """
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text=_("Name of the feature"),
        db_index=True
    )
    description = models.TextField(
        blank=True,
        help_text=_("Detailed description of the feature")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this feature is currently available")
    )

    class Meta:
        ordering = ['name']
        db_table = 'subscription_feature'
        verbose_name = _('Feature')
        verbose_name_plural = _('Features')

    def __str__(self) -> str:
        """Return string representation of the feature."""
        return self.name

    def __repr__(self) -> str:
        """Return detailed string representation for debugging."""
        return f"<Feature(id={self.id}, name='{self.name}', active={self.is_active})>"

    def clean(self) -> None:
        """Validate the model instance."""
        super().clean()
        if not self.name or not self.name.strip():
            raise ValidationError(_("Feature name cannot be empty"))
        
        self.name = self.name.strip()


class Plan(TimestampedModel):
    """
    Model representing a subscription plan with associated features.
    
    Plans define what features users get access to and serve as the
    foundation for user subscriptions.
    """
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text=_("Name of the subscription plan"),
        db_index=True
    )
    description = models.TextField(
        blank=True,
        help_text=_("Detailed description of the plan")
    )
    features = models.ManyToManyField(
        Feature,
        related_name='plans',
        blank=True,
        help_text=_("Features included in this plan")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this plan is currently available for subscription")
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Price of the plan (optional)")
    )

    class Meta:
        ordering = ['name']
        db_table = 'subscription_plan'
        verbose_name = _('Plan')
        verbose_name_plural = _('Plans')

    def __str__(self) -> str:
        """Return string representation of the plan."""
        return self.name

    def __repr__(self) -> str:
        """Return detailed string representation for debugging."""
        return (
            f"<Plan(id={self.id}, name='{self.name}', "
            f"active={self.is_active}, features_count={self.features.count()})>"
        )

    def clean(self) -> None:
        """Validate the model instance."""
        super().clean()
        if not self.name or not self.name.strip():
            raise ValidationError(_("Plan name cannot be empty"))
        
        if self.price is not None and self.price < 0:
            raise ValidationError(_("Price cannot be negative"))
        
        self.name = self.name.strip()

    def get_active_features(self):
        """Return only active features associated with this plan."""
        return self.features.filter(is_active=True)


class SubscriptionManager(models.Manager):
    """Custom manager for Subscription model."""
    
    def get_active_subscription_for_user(self, user: User):
        """
        Get the active subscription for a user.
        
        Args:
            user: The user to get the subscription for
            
        Returns:
            Subscription instance or None if no active subscription exists
        """
        try:
            return self.select_related('plan', 'user')\
                      .prefetch_related('plan__features')\
                      .get(user=user, is_active=True)
        except self.model.DoesNotExist:
            return None

    def get_optimized_queryset(self):
        """Return optimized queryset to avoid N+1 queries."""
        return self.select_related('plan', 'user')\
                  .prefetch_related('plan__features')


class Subscription(TimestampedModel):
    """
    Model representing a user's subscription to a plan.
    
    This model tracks the relationship between users and their chosen
    subscription plans, including activation status and dates.
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        help_text=_("User who owns this subscription")
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        help_text=_("Plan associated with this subscription")
    )
    start_date = models.DateTimeField(
        auto_now_add=True,
        help_text=_("When the subscription started")
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("When the subscription ended (if deactivated)")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this subscription is currently active")
    )
    notes = models.TextField(
        blank=True,
        help_text=_("Internal notes about this subscription")
    )

    objects = SubscriptionManager()

    class Meta:
        ordering = ['-created_at']
        db_table = 'subscription_subscription'
        verbose_name = _('Subscription')
        verbose_name_plural = _('Subscriptions')
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['plan', 'is_active']),
            models.Index(fields=['start_date']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(is_active=True),
                name='unique_active_subscription_per_user'
            )
        ]

    def __str__(self) -> str:
        """Return string representation of the subscription."""
        status = 'Active' if self.is_active else 'Inactive'
        return f"{self.user.username} - {self.plan.name} ({status})"

    def __repr__(self) -> str:
        """Return detailed string representation for debugging."""
        return (
            f"<Subscription(id={self.id}, user='{self.user.username}', "
            f"plan='{self.plan.name}', active={self.is_active})>"
        )

    def clean(self) -> None:
        """Validate the model instance."""
        super().clean()
        
        # Validate that start_date is before end_date if end_date is set
        if self.end_date and self.start_date and self.end_date <= self.start_date:
            raise ValidationError(_("End date must be after start date"))
        
        # Validate that inactive subscriptions have an end date
        if not self.is_active and not self.end_date:
            self.end_date = timezone.now()

    def deactivate(self, notes: str = "") -> None:
        """
        Deactivate the subscription.
        
        Args:
            notes: Optional notes about why the subscription was deactivated
        """
        if not self.is_active:
            logger.warning(f"Attempted to deactivate already inactive subscription {self.id}")
            return
        
        self.is_active = False
        self.end_date = timezone.now()
        if notes:
            self.notes = f"{self.notes}\n{notes}".strip()
        
        self.save(update_fields=['is_active', 'end_date', 'notes', 'updated_at'])
        
        logger.info(
            f"Subscription deactivated: User={self.user.username}, "
            f"Plan={self.plan.name}, Reason={notes or 'No reason provided'}"
        )
        
    @property
    def duration(self):
        """Get the duration of the subscription."""
        end_date = self.end_date or timezone.now()
        return end_date - self.start_date

    def has_feature(self, feature_name: str) -> bool:
        """
        Check if this subscription includes a specific feature.
        
        Args:
            feature_name: Name of the feature to check
            
        Returns:
            bool: True if the subscription includes the feature
        """
        return self.plan.features.filter(name=feature_name, is_active=True).exists()