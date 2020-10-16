"""Unit Tests for Wavefront Application Tags.

@author Shipeng Xie (xshipeng@vmware.com)
"""

import unittest
from unittest.mock import patch

from wavefront_sdk.common.application_tags import ApplicationTags


class TestApplicationTagsImpl(unittest.TestCase):
    """Unit Tests of ApplicationTags."""

    def setUp(self):
        """Initialize for tests."""
        self.env_patch = patch.dict(
            'os.environ', {
                'app_label_1': 'value_1',
                'app_label_2': 'value_2',
                'label_3': 'value_3'
            }, clear=True)
        self.application_tags = ApplicationTags(
            'test_app',
            'test_service',
            custom_tags=[('label_1', 'value_1')])
        self.env_patch.start()

    def tearDown(self):
        """Clean for tests."""
        self.env_patch.stop()

    def test_add_custom_tags_from_env(self):
        """Test add_custom_tags_from_env function."""
        self.assertEqual([('label_1', 'value_1')],
                         self.application_tags.custom_tags)
        self.application_tags.add_custom_tags_from_env(r'^App.*$')
        self.assertCountEqual([('label_1', 'value_1'),
                               ('app_label_1', 'value_1'),
                               ('app_label_2', 'value_2')],
                              self.application_tags.custom_tags)
        self.application_tags.add_custom_tags_from_env('app_tag')
        self.assertCountEqual([('label_1', 'value_1'),
                               ('app_label_1', 'value_1'),
                               ('app_label_2', 'value_2')],
                              self.application_tags.custom_tags)

    def test_add_custom_tag_from_env(self):
        """Test add_custom_tag_from_env function."""
        self.assertEqual([('label_1', 'value_1')],
                         self.application_tags.custom_tags)
        self.application_tags.add_custom_tag_from_env('label_2', 'app_label_2')
        self.assertCountEqual([('label_1', 'value_1'), ('label_2', 'value_2')],
                              self.application_tags.custom_tags)


if __name__ == '__main__':
    # run 'python -m unittest discover' from top-level to run tests
    unittest.main()
