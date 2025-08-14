import json
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.core.cache import cache
from decimal import Decimal
from .models import Feature, Plan, Subscription



class SubscriptionAPITestCase(APITestCase):
    """Test cases for Subscription API."""
    
    def setUp(self):
        """Set up test data."""
        # cache.clear()  # Clear cache before each test
        
        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2', 
            email='test2@example.com',
            password='testpass123'
        )
        
        # Create features
        self.feature1 = Feature.objects.create(
            name='Unlimited API Access',
            description='Access to unlimited API calls'
        )
        self.feature2 = Feature.objects.create(
            name='Priority Support',
            description='24/7 priority customer support'
        )
        self.feature3 = Feature.objects.create(
            name='Advanced Analytics',
            description='Advanced analytics and reporting'
        )
        
        # Create plans
        self.basic_plan = Plan.objects.create(
            name='Basic Plan',
            description='Basic features for small teams',
            price=Decimal('19.99')
        )
        self.basic_plan.features.add(self.feature1)
        
        self.pro_plan = Plan.objects.create(
            name='Pro Plan',
            description='Advanced features for growing teams',
            price=Decimal('49.99')
        )
        self.pro_plan.features.add(self.feature1, self.feature2, self.feature3)
        
        # Set up API client
        self.client = APIClient()
    
    def test_subscription_creation(self):
        """Test creating a new subscription."""
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('subscription-list')
        data = {'plan': self.basic_plan.id}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Subscription.objects.filter(user=self.user1).count(), 1)
        
        subscription = Subscription.objects.get(user=self.user1)
        self.assertEqual(subscription.plan, self.basic_plan)
        self.assertTrue(subscription.is_active)
    
    def test_subscription_creation_deactivates_existing(self):
        """Test that creating a new subscription deactivates existing active one."""
        self.client.force_authenticate(user=self.user1)
        
        # Create first subscription
        first_subscription = Subscription.objects.create(
            user=self.user1,
            plan=self.basic_plan
        )
        
        url = reverse('subscription-list')
        data = {'plan': self.pro_plan.id}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that first subscription is deactivated
        first_subscription.refresh_from_db()
        self.assertFalse(first_subscription.is_active)
        
        # Check that new subscription is active
        new_subscription = Subscription.objects.get(
            user=self.user1, 
            is_active=True
        )
        self.assertEqual(new_subscription.plan, self.pro_plan)
    
    def test_list_user_subscriptions(self):
        """Test listing user's subscriptions with nested data."""
        self.client.force_authenticate(user=self.user1)
        
        # Create subscriptions
        subscription = Subscription.objects.create(
            user=self.user1,
            plan=self.pro_plan
        )
        
        url = reverse('subscription-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        sub_data = response.data['results'][0]
        self.assertEqual(sub_data['id'], subscription.id)
        self.assertEqual(sub_data['plan']['name'], 'Pro Plan')
        self.assertEqual(len(sub_data['plan']['features']), 3)
        
        # Check feature details
        feature_names = [f['name'] for f in sub_data['plan']['features']]
        self.assertIn('Unlimited API Access', feature_names)
        self.assertIn('Priority Support', feature_names)
        self.assertIn('Advanced Analytics', feature_names)
    
    def test_change_subscription_plan(self):
        """Test changing a user's subscription plan."""
        self.client.force_authenticate(user=self.user1)
        
        subscription = Subscription.objects.create(
            user=self.user1,
            plan=self.basic_plan
        )
        
        url = reverse('subscription-change-plan', args=[subscription.id])
        data = {'plan': self.pro_plan.id}
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        subscription.refresh_from_db()
        self.assertEqual(subscription.plan, self.pro_plan)
        
        # Check response includes updated plan data
        self.assertEqual(response.data['plan']['name'], 'Pro Plan')
    
    def test_deactivate_subscription(self):
        """Test deactivating a subscription."""
        self.client.force_authenticate(user=self.user1)
        
        subscription = Subscription.objects.create(
            user=self.user1,
            plan=self.basic_plan
        )
        
        url = reverse('subscription-deactivate', args=[subscription.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        subscription.refresh_from_db()
        self.assertFalse(subscription.is_active)
        self.assertIsNotNone(subscription.end_date)
    
    def test_cannot_access_other_user_subscriptions(self):
        """Test that users cannot access other users' subscriptions."""
        # Create subscription for user2
        subscription = Subscription.objects.create(
            user=self.user2,
            plan=self.basic_plan
        )
        
        # Authenticate as user1
        self.client.force_authenticate(user=self.user1)
        
        # Try to access user2's subscription
        url = reverse('subscription-detail', args=[subscription.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated requests are denied."""
        url = reverse("subscription-list")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_invalid_plan_validation(self):
        """Test validation for invalid plan."""
        self.client.force_authenticate(user=self.user1)
        
        # Create inactive plan
        inactive_plan = Plan.objects.create(
            name='Inactive Plan',
            price=Decimal('29.99'),
            is_active=False
        )
        
        url = reverse('subscription-list')
        data = {'plan': inactive_plan.id}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Cannot subscribe to inactive plan', str(response.data))
    
    def test_get_active_subscription(self):
        """Test getting user's active subscription."""
        self.client.force_authenticate(user=self.user1)
        
        subscription = Subscription.objects.create(
            user=self.user1,
            plan=self.pro_plan
        )
        
        url = reverse('subscription-active-subscription')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], subscription.id)
        self.assertEqual(response.data['plan']['name'], 'Pro Plan')
    
    def test_no_active_subscription(self):
        """Test response when user has no active subscription."""
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('subscription-active-subscription')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('No active subscription found', response.data['message'])


class SubscriptionModelTestCase(TestCase):
    """Test cases for Subscription model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.feature = Feature.objects.create(name='Test Feature')
        self.plan = Plan.objects.create(
            name='Test Plan',
            price=Decimal('19.99')
        )
        self.plan.features.add(self.feature)
    
    def test_subscription_deactivate_method(self):
        """Test subscription deactivate method."""
        subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan
        )
        
        self.assertTrue(subscription.is_active)
        self.assertIsNone(subscription.end_date)
        
        subscription.deactivate()
        
        self.assertFalse(subscription.is_active)
        self.assertIsNotNone(subscription.end_date)