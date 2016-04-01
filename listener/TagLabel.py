#!/usr/bin/env python                                                                                                                                                
# -*- coding: utf-8 -*-

import os
import re
import logging
from robot.api import TestData
from robot.errors import DataError
from robot.writer.datafilewriter import DataFileWriter

from testrail import APIClient

TEST_RAIL_ID_TEMPLATE = 'testRailId={case_id}'
# todo: add other tags to existing test cases
TAG_TYPE = {
    'testRail': 'add_test_rail_id',
    'defects': 'add_defects',
    'references': 'add_references'
}


def getTagsValue(tags):
    """
    Get value from robot framework's tags for TestRail.
    """
    attributes = dict()
    matchers = ['testRailId', 'defects', 'references']
    for matcher in matchers:
        for tag in tags:
            match = re.match(matcher, tag)
            if match:
                split_tag = tag.split('=')
                tag_value = split_tag[1]
                attributes[matcher] = tag_value
                break
            else:
                attributes[matcher] = None
    return attributes


class TestRailTagger(object):
    """
    class to register robot's test cases in test rail
    and then add corresponding tags to robot's test cases
    """

    def __init__(self, host, user, password,
                 file_path, section_id,
                 file_format='robot'):
        """
        :param host: test rail host
        :param user: user name
        :param password: password
        :param file_path: path of test case files or directory
        :param section_id: section to store auto test cases
        :param file_format: default to be .robot
        """
        testrail_url = 'http://' + host + '/testrail/'
        self.client = APIClient(testrail_url, user, password)
        self.file = list()
        # to loop through the test suites
        try:
            if os.path.isdir(file_path):
                for files in os.walk(file_path):
                    for robot_file in filter(lambda x: x.endswith('.robot'), files[2]):
                            self.file.append(
                                TestData(
                                    source=os.path.abspath(os.path.join(files[0],
                                                                        robot_file))
                                )
                            )
            else:
                self.file.append(TestData(source=file_path))
        except DataError as e:
            # .robot file may have no test cases in it
            logging.warn('[TestRailTagger]' + e.message)

        self.section = section_id
        self.writer = DataFileWriter(format=file_format)

    def add_tag(self):
        """
        add specific tags to test cases
        """
        for suite in self.file:
            # to handle force tags, delete force tags in setting table
            # and then add the tag value to each test case in a suite
            force_tags = suite.setting_table.force_tags.value
            suite.setting_table.force_tags.value = None
            for test in suite.testcase_table.tests:
                getattr(self, TAG_TYPE['testRail'])(test, suite, force_tags)

    def add_test_rail_id(self, test, test_case_file, other_tags):
        """
        register test case and add the test case id to .robot file
        :param test: TestData class object, one of test cases
                    read from goven .robot file
        :param test_case_file: the .robot file to write (add tags)
        :param other_tags: param for the force tags(also for other tags)
        """
        if test.tags.value is None:
            test.tags.value = list()
        tags_value = getTagsValue(test.tags.value)
        case_id = tags_value.get('testRailId')
        if case_id is None:
            res = self.client.send_post(
                        'add_case/{section_id}'.format(section_id=self.section),
                        {
                            'title': 'Auto-' + test.name,
                            'type_id': 1,
                            'priority_id': 3,
                            'estimate': '1h',
                            'refs': '',
                            'custom_steps': [
                                {
                                    'content': getattr(step, 'name', ''),
                                    'expected': 'auto-results'
                                } for step in test.steps if step
                            ]
                        }
                    )
            case_id = res.get('id')
            logging.info('[TestRailTagger] register test {case_id} to TestRail'
                         .format(case_id=case_id))
            test.tags.value.append(TEST_RAIL_ID_TEMPLATE.format(case_id=case_id))
            test.tags.value += other_tags
            self.writer.write(test_case_file)
