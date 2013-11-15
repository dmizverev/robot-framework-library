# -*- coding: utf-8 -*-

from robot.api import logger
from TestlinkAPIClient import TestlinkAPIClient as testlink

class TestLinkListener(object):
    """
    Фиксирование результатов тестирования в TestLink.\n
    
    """

    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self, testlinkuri, devKey, testplanID):
        self.server = 'http://'+testlinkuri+'/testlink/lib/api/xmlrpc.php'
        self.devKey = devKey
        self.testplanID = testplanID
        self.tl = testlink(self.server,self.devKey,self.testplanID)
        self.buildID = self.tl.getLatestBuildForTestPlan()
        logger.info('[TestLinkListener] server url: ' + self.server)
        logger.info('[TestLinkListener] developer key: ' + self.devKey)
        logger.info('[TestLinkListener] testplanID: ' + self.testplanID)
        logger.info('[TestLinkListener] buildID: ' + self.buildID)

    def end_test(self, name, attrs):
        """
        Сохранение результата выполнения теста в TestLink
        
        Входные параметры:\n
        name - имя тест-кейса\n
        attrs - атрибуты теста
        """
        testcaseID = self.tl.getTestCaseIDFromTestTags (attrs['tags'])
        if attrs['status'] == 'PASS':
            status = 'p'
        else :
            status = 'f'
        if testcaseID:
            self.tl.reportTCResult (testcaseID,self.buildID,status,attrs['message'])
            logger.info ('[TestLinkListener] report result of test ' + testcaseID + ' to TestLink')
