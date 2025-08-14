from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.contrib.auth.models import User
from .models import Subscription, Plan, Feature
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Subscription)
def subscription_post_save(sender, instance, created, **kwargs):
    """Clear cache when subscription is saved."""
    # Clear user's subscription cache
    cache.delete(f"user_subscriptions_{instance.user.id}")
    cache.delete(f"active_subscription_{instance.user.id}")
    
    if created:
        logger.info(f"New subscription created: {instance.id} for user {instance.user.username}")
    else:
        logger.info(f"Subscription updated: {instance.id}")


@receiver(post_delete, sender=Subscription)
def subscription_post_delete(sender, instance, **kwargs):
    """Clear cache when subscription is deleted."""
    cache.delete(f"user_subscriptions_{instance.user.id}")
    cache.delete(f"active_subscription_{instance.user.id}")
    logger.info(f"Subscription deleted: {instance.id}")


@receiver(post_save, sender=Plan)
def plan_post_save(sender, instance, **kwargs):
    """Clear plan cache when plan is updated."""
    cache.delete_many([
        f"plan_{instance.id}",
        "plans_list"
    ])
    logger.info(f"Plan cache cleared for: {instance.name}")


@receiver(post_save, sender=Feature)
def feature_post_save(sender, instance, **kwargs):
    """Clear related caches when feature is updated."""
    # Clear all plan caches since features might be linked to plans
    cache.delete("plans_list")
    
    # Clear subscription caches for plans that have this feature
    for plan in instance.plans.all():
        for subscription in plan.subscriptions.all():
            cache.delete(f"user_subscriptions_{subscription.user.id}")
            cache.delete(f"active_subscription_{subscription.user.id}")
    
    logger.info(f"Feature cache cleared for: {instance.name}")
