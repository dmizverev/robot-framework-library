# -*- coding: utf-8 -*-

import re
from robot.api import logger
from testrail import *

__author__ = "Dmitriy.Zverev"
__license__ = "Apache License, Version 2.0"

class TestRailListener(object):
    """
    Fixing of testing results and update test case in [ http://www.gurock.com/testrail/ | TestRail ].\n
    == Dependency ==
    - [ http://docs.gurock.com/testrail-api2/bindings-python | TestRail API2 python binding]
    == Preconditions ==
    1. [ http://docs.gurock.com/testrail-api2/introduction | Enable TestRail API] \n
    2. Create custom field "case_description" with type "text", which corresponds to the Robot Framework's test case documentation.
    == Example ==
    1. Create test case in TestRail with case_id = 10\n
    2. Add it to test run with id run_id = 20\n
    3. Create autotest in Robot Framework
    | *** Settings ***
    | *** Test Cases ***
    | Autotest name
    |    [Documentation]    Autotest documentation
    |    [Tags]    testrailid=10
    |    Fail    Test fail message
    4. Run Robot Framework with listener:\n
    | set ROBOT_SYSLOG_FILE=syslog.txt
    | pybot.bat --listener TestRailListener.py:testrail_server_name:tester_user_name:tester_user_password:20:update  autotest.txt
    5. Test with case_id=10 will be marked as failed in TestRail with message "Test fail message". 
    Also title and description of this test will be updated in TestRail. Parameter "update" is optional.
    """

    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self, server, user, password, run_id, update = None):
        """
        *Args:*\n
        _server_ - the name of TestRail server;
        _user_ - the name of TestRail user;
        _password_ - the password of TestRail user;
        _run_id -  the ID of the test run;
        _update_ - indicator to update test case in TestRail; if exist, then test will be updated.
        """

        testrail_url = 'http://' + server + '/testrail/'
        self.client = APIClient(testrail_url)
        self.client.user = user
        self.client.password = password
        self.run_id = run_id
        self.update = update
        logger.info('[TestRailListener] url: ' + testrail_url)
        logger.info('[TestRailListener] user: ' + user)
        logger.info('[TestRailListener] password: ' + password)
        logger.info('[TestRailListener] the ID of the test run: ' + run_id)

    def end_test(self, name, attrs):
        """
        Save test result in TestRail
        
        *Args:*\n
        _name_ - the name of test case in Robot Framework\n
        _attrs_ - attributes of test case in Robot Framework
        """

        case_id = self._getTestCaseIDFromTestTags (attrs['tags'])
        if attrs['status'] == 'PASS':
            status_id = 1
        else :
            status_id = 5
        if case_id:
            # Update test case
            if self.update:
                logger.info ('[TestRailListener] update of test ' + case_id + ' in TestRail')
                description = attrs['doc'] + '\n' + 'Path to test: ' + attrs['longname']
                result = self.client.send_post(
                                               'update_case/' + case_id,
                                               { 'title': name, 'type_id': 1, 'custom_case_description': description}
                )
                logger.info ('[TestRailListener] result for method update_case ' + json.dumps(result, sort_keys = True, indent = 4))
            # Set test result
            logger.info ('[TestRailListener] report result of test ' + case_id + ' to TestRail')
            result = self.client.send_post(
                                           'add_result_for_case/' + self.run_id + '/' + case_id,
                                           { 'status_id': status_id, 'comment': attrs['message'] }
            )
            logger.info ('[TestRailListener] result for method add_result_for_case ' + json.dumps(result, sort_keys = True, indent = 4))


    def _getTestCaseIDFromTestTags(self, tags):
        """ 
        Getting the TestRail's case_id from the tag that should exist in the autotest.
        
        *Args:*\n
        _tags_ - list of tags in autotest;\n
        
        *Returns:*\n
        case_id for TestRail
        
        *Example:*\n
        [Tags]    testrailid=10\n
        =>\n
        case_id = 40
        """

        match_tag = 'testrailid'
        for tag in tags:
            match = re.match(match_tag, tag)
            if match :
                split_tag = tag.split('=')
                testcaseID = split_tag[1]
                return testcaseID
