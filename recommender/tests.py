from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from recommender.models import UserProfile, Prediction
from recommender.ml.loader import load_bundle
from unittest.mock import patch
import time

class AuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='test@test.com', email='test@test.com', password='password123', first_name='Test', last_name='User')
        UserProfile.objects.create(user=self.user, phone='1234567890')

    def test_login_success(self):
        response = self.client.post(reverse('login'), {'email': 'test@test.com', 'password': 'password123'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)

    def test_login_failure(self):
        response = self.client.post(reverse('login'), {'email': 'test@test.com', 'password': 'wrongpassword'}, follow=True)
        self.assertFalse(response.context['user'].is_authenticated)

    def test_signup(self):
        response = self.client.post(reverse('signup'), {
            'full_name': 'New User',
            'phone': '0987654321',
            'email': 'new@test.com',
            'password': 'password123'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username='new@test.com').exists())
        self.assertTrue(UserProfile.objects.filter(phone='0987654321').exists())

    def test_duplicate_signup(self):
        response = self.client.post(reverse('signup'), {
            'full_name': 'Another User',
            'phone': '111222333',
            'email': 'test@test.com',
            'password': 'password123'
        }, follow=True)
        # Should redirect to signup and have messages
        self.assertEqual(User.objects.filter(username='test@test.com').count(), 1)

class PredictionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='pred@test.com', email='pred@test.com', password='password123', first_name='Pred', last_name='User')
        UserProfile.objects.create(user=self.user, phone='1234567890')
        self.client.login(username='pred@test.com', password='password123')

    def test_predict_get(self):
        # GET should not load the ML model. We can use patch to spy on load_bundle
        with patch('recommender.views.predict_one') as mock_predict:
            response = self.client.get(reverse('predict'))
            self.assertEqual(response.status_code, 200)
            self.assertIn('feature_order', response.context)
            mock_predict.assert_not_called()

    def test_predict_post_valid(self):
        data = {
            'N': 10, 'P': 10, 'K': 10,
            'temperature': 20, 'humidity': 50,
            'ph': 6, 'rainfall': 100
        }
        response = self.client.post(reverse('predict'), data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('result', response.context)
        self.assertTrue(Prediction.objects.filter(user=self.user).exists())

    def test_predict_post_invalid(self):
        data = {
            'N': 'invalid', 'P': 10, 'K': 10,
            'temperature': 20, 'humidity': 50,
            'ph': 6, 'rainfall': 100
        }
        response = self.client.post(reverse('predict'), data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Prediction.objects.filter(user=self.user).exists())

    def test_missing_model_graceful_handling(self):
        data = {
            'N': 10, 'P': 10, 'K': 10,
            'temperature': 20, 'humidity': 50,
            'ph': 6, 'rainfall': 100
        }
        with patch('recommender.views.predict_one', side_effect=Exception("Model unavailable")):
            response = self.client.post(reverse('predict'), data, follow=True)
            self.assertEqual(response.status_code, 200)
            messages = list(response.context['messages'])
            self.assertTrue(any("Unable to perform prediction" in str(msg) for msg in messages))

class PasswordChangeTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='pwd@test.com', email='pwd@test.com', password='password123')
        self.client.login(username='pwd@test.com', password='password123')

    def test_password_change(self):
        response = self.client.post(reverse('change_password'), {
            'current_password': 'password123',
            'new_password': 'newpassword123',
            'confirm_new_password': 'newpassword123'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('_auth_user_id' in self.client.session)

        # Logout and login with new password
        self.client.logout()
        login_response = self.client.post(reverse('login'), {'email': 'pwd@test.com', 'password': 'newpassword123'}, follow=True)
        self.assertTrue(login_response.context['user'].is_authenticated)

class AdminTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(username='admin@test.com', email='admin@test.com', password='adminpassword')
        self.client.login(username='admin@test.com', password='adminpassword')

    def test_admin_dashboard(self):
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_admin_users_view(self):
        # Generate some users
        User.objects.create_user(username='u1@test.com', email='u1@test.com', password='123')
        User.objects.create_user(username='u2@test.com', email='u2@test.com', password='123')

        with self.assertNumQueries(3): # Should not be N+1
            response = self.client.get(reverse('admin_view_users'))
        self.assertEqual(response.status_code, 200)
