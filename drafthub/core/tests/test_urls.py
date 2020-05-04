from django.test import TestCase
from django.urls import reverse, resolve
from django.contrib.auth import views as auth_views

from drafthub.draft.models import Blog
from social_django.models import UserSocialAuth
from drafthub.core.views import (
    HomeView, SearchListView, LoginView, BlogUpdateView, BlogListView
)


class HomeUrlsTestCase(TestCase):
    def test_home_view_class(self):
        url = reverse('home')
        self.assertEqual(resolve(url).func.view_class, HomeView)

    def test_home_status_code(self):
        url = reverse('home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class SearchUrlsTestCase(TestCase):
    def test_search_view_class(self):
        url = reverse('search')
        self.assertEqual(resolve(url).func.view_class, SearchListView)

    def test_search_status_code(self):
        url = reverse('search')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class LogoutUrlsSimpletestCase(TestCase):
    def test_logout_view_class(self):
        url = reverse('logout')
        self.assertEqual(resolve(url).func.view_class, auth_views.LogoutView)

    def test_logout_status_code(self):
        url = reverse('logout')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)


class LoginUrlsSimpletestCase(TestCase):
    def test_login_view_class(self):
        url = reverse('login')
        self.assertEqual(resolve(url).func.view_class, LoginView)

    def test_login_status_code(self):
        url = reverse('login')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class EditUrlsSimpletestCase(TestCase):
    def test_edit_view_class(self):
        url = reverse('edit')
        self.assertEqual(resolve(url).func.view_class, BlogUpdateView)

    def test_edit_status_code(self):
        url = reverse('edit')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)


class BlogUrlsSimpletestCase(TestCase):
    def setUp(self):
        blog = Blog.objects.create(username='test')
        UserSocialAuth.objects.create(user=blog)

    def test_blog_view_class(self):
        url = reverse('blog', args=('test',)) 
        self.assertEqual(resolve(url).func.view_class, BlogListView)

    def test_blog_not_found(self):
        url = reverse('blog', args=(' ',))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_blog_status_code(self):
        url = reverse('blog', args=('test',))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
