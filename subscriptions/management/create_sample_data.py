from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from ..models import Feature, Plan, Subscription


class Command(BaseCommand):
    help = 'Create sample data for testing the subscription API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Clean existing data before creating new data',
        )

    def handle(self, *args, **options):
        if options['clean']:
            self.stdout.write('Cleaning existing data...')
            Subscription.objects.all().delete()
            Plan.objects.all().delete()
            Feature.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

        # Create features
        self.stdout.write('Creating features...')
        features = [
            ('Basic API Access', 'Access to basic API endpoints with rate limiting'),
            ('Unlimited API Access', 'Unlimited access to all API endpoints'),
            ('Priority Support', '24/7 priority customer support'),
            ('Advanced Analytics', 'Advanced analytics and reporting dashboard'),
            ('Custom Integrations', 'Custom integration development support'),
            ('White Label', 'White label solution for your brand'),
            ('SSO Integration', 'Single Sign-On integration'),
            ('Data Export', 'Export data in various formats'),
            ('Real-time Notifications', 'Real-time push notifications'),
            ('Multi-user Access', 'Team collaboration features'),
        ]

        feature_objects = []
        for name, description in features:
            feature, created = Feature.objects.get_or_create(
                name=name,
                defaults={'description': description}
            )
            feature_objects.append(feature)
            if created:
                self.stdout.write(f'Created feature: {name}')

        # Create plans
        self.stdout.write('Creating plans...')
        plans_data = [
            {
                'name': 'Starter',
                'description': 'Perfect for individuals and small projects',
                'price': Decimal('9.99'),
                'features': [0]  # Basic API Access
            },
            {
                'name': 'Professional',
                'description': 'Ideal for growing businesses and teams',
                'price': Decimal('29.99'),
                'features': [1, 2, 3, 7]  # Unlimited API, Support, Analytics, Data Export
            },
            {
                'name': 'Business',
                'description': 'Advanced features for established businesses',
                'price': Decimal('79.99'),
                'features': [1, 2, 3, 4, 6, 7, 8, 9]  # Most features except White Label
            },
            {
                'name': 'Enterprise',
                'description': 'Complete solution for large organizations',
                'price': Decimal('199.99'),
                'features': list(range(len(feature_objects)))  # All features
            }
        ]

        plan_objects = []
        for plan_data in plans_data:
            plan, created = Plan.objects.get_or_create(
                name=plan_data['name'],
                defaults={
                    'description': plan_data['description'],
                    'price': plan_data['price']
                }
            )
            
            # Add features to plan
            plan.features.clear()
            for feature_idx in plan_data['features']:
                plan.features.add(feature_objects[feature_idx])
            
            plan_objects.append(plan)
            if created:
                self.stdout.write(f'Created plan: {plan.name} - ${plan.price}')

        # Create sample users
        self.stdout.write('Creating sample users...')
        users_data = [
            ('john_doe', 'john@example.com', 'John', 'Doe'),
            ('jane_smith', 'jane@example.com', 'Jane', 'Smith'),
            ('bob_wilson', 'bob@example.com', 'Bob', 'Wilson'),
        ]

        for username, email, first_name, last_name in users_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
                self.stdout.write(f'Created user: {username}')

                # Create a subscription for each user (alternating plans)
                plan_idx = len(User.objects.filter(username__in=[u[0] for u in users_data])) % len(plan_objects)
                subscription = Subscription.objects.create(
                    user=user,
                    plan=plan_objects[plan_idx]
                )
                self.stdout.write(f'Created subscription for {username} with {plan_objects[plan_idx].name} plan')

        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        )