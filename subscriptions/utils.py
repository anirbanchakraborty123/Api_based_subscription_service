from django.core.cache import cache
from django.db.models import QuerySet
from typing import Any, Optional
import hashlib
import json


def get_cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate a cache key from prefix and arguments."""
    key_parts = [prefix]
    
    # Add positional arguments
    for arg in args:
        if isinstance(arg, (int, str)):
            key_parts.append(str(arg))
        else:
            key_parts.append(str(hash(str(arg))))
    
    # Add keyword arguments
    if kwargs:
        sorted_kwargs = sorted(kwargs.items())
        kwargs_str = json.dumps(sorted_kwargs, sort_keys=True)
        kwargs_hash = hashlib.md5(kwargs_str.encode()).hexdigest()[:8]
        key_parts.append(kwargs_hash)
    
    return "_".join(key_parts)


def cached_queryset(cache_key: str, queryset_func, timeout: int = 300) -> QuerySet:
    """Cache queryset results."""
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data
    
    data = queryset_func()
    cache.set(cache_key, data, timeout=timeout)
    return data


def invalidate_user_cache(user_id: int):
    """Invalidate all cache entries for a specific user."""
    cache_keys = [
        f"user_subscriptions_{user_id}",
        f"active_subscription_{user_id}",
    ]
    cache.delete_many(cache_keys)