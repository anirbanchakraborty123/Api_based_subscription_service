from django.contrib import admin
from .models import Feature, Plan, Subscription


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_active', 'feature_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    filter_horizontal = ('features',)
    readonly_fields = ('created_at', 'updated_at')
    
    def feature_count(self, obj):
        return obj.features.count()
    feature_count.short_description = 'Features'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'is_active', 'start_date', 'end_date')
    list_filter = ('is_active', 'plan', 'start_date')
    search_fields = ('user__username', 'user__email', 'plan__name')
    readonly_fields = ('start_date', 'created_at', 'updated_at')
    raw_id_fields = ('user', 'plan')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'plan')
