from django.utils import unittest
from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.http import HttpRequest
from django.test.client import Client
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse

from uploadeXe.models import Role
from uploadeXe.models import User_Roles
from django.forms import ModelForm
from organisation.models import Organisation
from organisation.models import UMCloud_Package
from organisation.models import User_Organisations
from users.models import UserProfile
from django import forms



class UserTestCase(TestCase):
    def setUp(self):
        User.objects.create(username="unittestuser",email="unittestuser@ustadmobile.com",password="holycow")
    def test_basic_addition(self):
        """
        Tests that 1+1 is always 2
        """
        self.assertEqual(1+1,2)
    def test_user_created(self):
        """
        Tests that the user is actually created and assigned an active flag
        """
        unittestuser = User.objects.get(username="unittestuser",password="holycow")
        self.assertEqual(unittestuser.is_active, True)

    def tearDown(self):
        print("End of User creation test.")

class BaseAssertionTest(TestCase):

    def test_some_assertions(self):
        """
        Testing assertions in python 
        """
        self.assertTrue(1)
        self.assertFalse(0)
        self.assertEquals(1,1)
        self.assertNotEquals(1,2)

        """
        Testing Python 2.7 assertions
        """
        o = 1
        self.assertIs(o,o)
        self.assertIn(1, [1,2,3])
        self.assertIsInstance(self, TestCase)

        """
        Emulates requests so that we can test views
        """
        """
        self.assertRedirects(response, expected_url, status_code, target_status_code)
        self.assertContains(response, text, count, status_code)
        self.assertNotContains(response, text, count, status_code)
        self.assertFormError(response, form, field, errors)
        self.assertTemplateUsed(response, template_name)
        self.assertTemplateNotUsed(response, template_name)
        self.assertQuerysetEqual(qs, values)
        """

    def tearDown(self):
        print("End of Python assertion test")

