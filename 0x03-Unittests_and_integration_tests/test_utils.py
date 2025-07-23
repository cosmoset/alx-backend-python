#!/usr/bin/env python3
'''
Unit test for utils
'''
import unittest
from utils import *
from parameterized import parameterized
from unittest.mock import patch, MagicMock
import requests
import json
from typing import (
    Mapping,
    Sequence,
    Any,
    Dict,
    Callable,
)


class TestAccessNestedMap(unittest.TestCase):
    '''
    Class to test access nested map
    '''

    @parameterized.expand([
        ({}, ("a",), 'a'),
        ({"a": 1}, ("a", "b"), 'b')
    ])
    def test_access_nested_map_exception(
                  self, nested_map, path, key_error):
        '''
        function to test access_nested_map exception
        '''

        with self.assertRaises(KeyError) as cm:
            access_nested_map(nested_map, path)

        nested_map_exception = cm.exception
        self.assertEqual(str(nested_map_exception), f"'{key_error}'")

    @parameterized.expand([
        ({"a": 1}, ("a",), 1),
        ({"a": {"b": 2}}, ("a",), {"b": 2}),
        ({"a": {"b": 2}}, ("a", "b"), 2)
    ])
    def test_access_nested_map(
            self, nested_map: Mapping, path: Sequence, expected_output):
        '''
        Function to test access_nested_map from utils
        '''
        result = access_nested_map(nested_map, path)
        self.assertEqual(result, expected_output)


class TestGetJson(unittest.TestCase):
    '''
    Class to test get json
    '''
    @parameterized.expand([
        ("http://example.com", {"payload": True}),
        ("http://holberton.io", {"payload": False})
    ])
    @patch('requests.get')
    def test_get_json(self, test_url, test_payload, mock_request):
        '''
        Function to test get_json
        '''

        mock_request.return_value.json.return_value = test_payload

        payload = get_json(test_url)
        self.assertEqual(payload, test_payload)


class TestMemoize(unittest.TestCase):
    '''
    A class to test memorize function
    '''
    class TestClass:
        '''
        Test class
        '''

        def a_method(self):
            '''
            Function to return 42
            '''
            return 42

        @memoize
        def a_property(self):
            '''
            function to be memorized by decorator
            '''
            return self.a_method()

    def test_memoize(self):
        '''
        Function to test memorize
        '''
        with patch.object(self.TestClass, 'a_method') as mock_a_method:
            mock_a_method.return_value = 42

            instance = self.TestClass()
            result1 = instance.a_property
            result2 = instance.a_property

            mock_a_method.assert_called_once()

            self.assertEqual(result1, 42)
            self.assertEqual(result2, 42)


if __name__ == '__main__':
    unittest.main()
