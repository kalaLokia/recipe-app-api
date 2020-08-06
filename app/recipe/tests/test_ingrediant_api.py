from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingrediant, Recipe

from recipe.serializers import IngrediantSerializer


INGREDIANT_URL = reverse('recipe:ingrediant-list')


class PublicIngrediantApiTests(TestCase):
    """Test the publicaly available ingrediants API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required to access the endpoint"""
        res = self.client.get(INGREDIANT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngrediantApiTests(TestCase):
    """Test the private ingrediants API"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test@kalalokia.com',
            'testpass'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_ingrediant(self):
        """Test retrieving a list of ingrediants"""
        Ingrediant.objects.create(user=self.user, name='Kale')
        Ingrediant.objects.create(user=self.user, name='Salt')

        res = self.client.get(INGREDIANT_URL)

        Ingrediants = Ingrediant.objects.all().order_by('-name')
        serializer = IngrediantSerializer(Ingrediants, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingrediants_limited_to_user(self):
        """Test that ingrediants for the authenticated user are returned"""
        user2 = get_user_model().objects.create_user(
            'other@kalalokia.com',
            'testpass'
        )
        Ingrediant.objects.create(user=user2, name='Vinegar')
        ingrediant = Ingrediant.objects.create(user=self.user, name='Tumeric')

        res = self.client.get(INGREDIANT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingrediant.name)

    def test_create_ingrediant_successful(self):
        """Test create a new ingrediant"""
        payload = {'name': 'Cabbage'}
        self.client.post(INGREDIANT_URL, payload)

        exists = Ingrediant.objects.filter(
            user=self.user,
            name=payload['name'],
        ).exists()
        self.assertTrue(exists)

    def test_create_ingrediant_invalid(self):
        """Test creating invalid ingrediant fails"""
        payload = {'name': ''}
        res = self.client.post(INGREDIANT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_ingrediants_assigned_to_recipes(self):
        """Test filtering tags by those assigned to recipes"""
        ingrediant1 = Ingrediant.objects.create(user=self.user, name='Chilly')
        ingrediant2 = Ingrediant.objects.create(user=self.user, name='Sugar')
        recipe = Recipe.objects.create(
            title='Egg burjjy',
            time_minutes=7,
            price=30,
            user=self.user
        )
        recipe.ingrediants.add(ingrediant1)

        res = self.client.get(INGREDIANT_URL, {'assigned_only': 1})

        serializer1 = IngrediantSerializer(ingrediant1)
        serializer2 = IngrediantSerializer(ingrediant2)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retireve_unique_ingrediants(self):
        """Test filtering ingrediants by assigned returns unique items"""
        ingrediant = Ingrediant.objects.create(user=self.user, name='Chilly')
        Ingrediant.objects.create(user=self.user, name='Tomato')
        recipe1 = Recipe.objects.create(
            title='Egg burjjy',
            time_minutes=7,
            price=30,
            user=self.user
        )
        recipe1.ingrediants.add(ingrediant)
        recipe2 = Recipe.objects.create(
            title='Chicken chukka',
            time_minutes=29,
            price=130,
            user=self.user
        )
        recipe2.ingrediants.add(ingrediant)

        res = self.client.get(INGREDIANT_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
