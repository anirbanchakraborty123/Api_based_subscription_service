from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


def validate_positive_price(value):
    """Validate that price is positive."""
    if value < 0:
        raise ValidationError(
            _('Price must be positive'),
            params={'value': value},
        )


def validate_plan_name(value):
    """Validate plan name format."""
    if not value.strip():
        raise ValidationError(_('Plan name cannot be empty'))
    
    if len(value.strip()) < 2:
        raise ValidationError(_('Plan name must be at least 2 characters long'))
    
    return value.strip()


def validate_feature_name(value):
    """Validate feature name format."""
    if not value.strip():
        raise ValidationError(_('Feature name cannot be empty'))
    
    if len(value.strip()) < 3:
        raise ValidationError(_('Feature name must be at least 3 characters long'))
    
    return value.strip()