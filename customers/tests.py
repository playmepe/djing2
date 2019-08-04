from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from rest_framework.test import APITestCase
from customers import models
from services.models import Service


UserProfile = get_user_model()


class CustomAPITestCase(APITestCase):
    def get(self, *args, **kwargs):
        return self.client.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        return self.client.post(*args, **kwargs)

    def setUp(self):
        UserProfile.objects.create_superuser(
            username='admin',
            password='admin',
            telephone='+797812345678'
        )
        self.client.login(
            username='admin',
            password='admin'
        )


class CustomerServiceTestCase(CustomAPITestCase):
    def test_direct_create(self):
        r = self.post('/api/customers/customer-service/')
        self.assertEqual(r.data, _("Not allowed to direct create Customer service, use 'pick_service' url"))
        self.assertEqual(r.status_code, 403)


class CustomerLogAPITestCase(CustomAPITestCase):
    def test_direct_create(self):
        r = self.post('/api/customers/customer-log/')
        self.assertEqual(r.data, _("Not allowed to direct create Customer log"))
        self.assertEqual(r.status_code, 403)


class CustomerModelAPITestCase(CustomAPITestCase):
    def setUp(self):
        super().setUp()

        # customer for tests
        self.post('/api/customers/', {
            'username': 'custo1',
            'fio': 'Full User Name',
            'password': 'passw',
        })
        self.customer = models.Customer.objects.get(username='custo1')

        # service for tests
        self.service = Service.objects.create(
            title='test service',
            speed_in=10.0,
            speed_out=10.0,
            cost=2,
            calc_type=0  # ServiceDefault
        )

    def test_get_random_username(self):
        r = self.get('/api/customers/generate_username/')
        random_unique_uname = r.data
        qs = models.Customer.objects.filter(username=random_unique_uname)
        self.assertFalse(qs.exists())

    def test_pick_service_not_enough_money(self):
        self.customer.refresh_from_db()
        r = self.post('/api/customers/%d/pick_service/' % self.customer.pk, {
            'service_id': self.service.pk,
            'deadline': (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%dT%H:%M')
        })
        self.assertEqual(r.data, _('%(uname)s not enough money for service %(srv_name)s') % {
            'uname': self.customer.username,
            'srv_name': self.service.title
        })
        self.assertEqual(r.status_code, 400)
