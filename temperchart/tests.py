from django.test import TestCase
from requests import Response
from rest_framework.test import APIClient

from ea.tests import InitData


class TemperChartTest(InitData, TestCase):

    def setUp(self) -> None:
        self.position_create()
        self.department_create()

        self.user = self.user_create('swl21803', 'swl21803', '이승우')
        self.user.set_password('swl21803')
        self.user.save()

        token: str = self.login(self.client)
        self.drf_client = APIClient()
        self.drf_client.credentials(HTTP_AUTHORIZATION='Token ' + token)

    def test_get_chart_data_view(self):
        data = {'startDate': '2020-07-27', 'endDate': '2020-07-28'}
        response: Response = self.drf_client.get('/temperchart/get_chart_data/', data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
