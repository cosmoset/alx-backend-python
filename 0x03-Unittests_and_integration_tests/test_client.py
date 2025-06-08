#!/usr/bin/env python3

from unittest import TestCase
from unittest.mock import patch, Mock, PropertyMock
from parameterized import parameterized
from fixtures import TEST_PAYLOAD
from client import GithubOrgClient


class TestGithubOrgClient(TestCase):
    @parameterized.expand(
        [
            ("google", TEST_PAYLOAD),
            ("abc", TEST_PAYLOAD),
        ]
    )
    def test_org(self, org_name, test_payload):
        with patch("requests.get") as mock_requests_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = test_payload

            mock_requests_get.return_value = mock_response
            github_org_client = GithubOrgClient(org_name)
            self.assertEqual(github_org_client.org, test_payload)

    @parameterized.expand([(TEST_PAYLOAD[0][0],)])
    def test_public_repos_url(self, test_payload):
        with patch.object(
            GithubOrgClient,
            "org",
            new_callable=PropertyMock,
        ) as mock_GithubOrgClient:
            mock_GithubOrgClient.return_value = test_payload
            self.assertEqual(
                GithubOrgClient("google")._public_repos_url,
                "https://api.github.com/orgs/google/repos",
            )

    # ? Why does making patch decorator and the mock json first not work????
    @parameterized.expand([("google", TEST_PAYLOAD[0][0])])
    @patch("utils.get_json")
    def test_public_repos(
        self,
        org_name,
        test_payload,
        mock_get_json,
    ):
        mock_get_json.return_value = test_payload
        with patch.object(
            GithubOrgClient, "_public_repos_url", new_callable=PropertyMock
        ) as mock__public_repos_url:
            mock__public_repos_url.return_value = test_payload["repos_url"]
            self.assertEqual(
                GithubOrgClient(org_name)._public_repos_url,
                "https://api.github.com/orgs/google/repos",
            )

    @parameterized.expand(
        [
            ({"license": {"key": "my_license"}}, "my_license", True),
            ({"license": {"key": "other_license"}}, "my_license", False),
        ]
    )
    def test_has_license(self, repo, license_key, test_result):
        self.assertEqual(GithubOrgClient.has_license(repo, license_key), test_result)


class TestIntegrationGithubOrgClient(TestCase):
    def setUp(self):
        return super().setUp()

    def tearDown(self):
        return super().tearDown()

    def setUpClass(self):
        return self.setUp()

    def tearDownClass(self):
        return self.tearDown()

    @parameterized.expand(
        [
            (0, TEST_PAYLOAD[0]),
            (1, TEST_PAYLOAD[0])(2, TEST_PAYLOAD[0])(3, TEST_PAYLOAD[0]),
        ]
    )
    def get_patcher(self, test_index, test_payload):
        with patch("requests.get") as mock_requests_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = test_payload[test_index]

            mock_requests_get.return_value = mock_response
