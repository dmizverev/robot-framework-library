# -*- coding: utf-8 -*-
import xmlrpclib
import re
from robot.api import logger

class TestlinkAPIClient:
    """
    Реализация API взаимодействия с TestLink.
    """

    def __init__(self, server, devKey, testplanID=None):
        """
        Входные параметры:\n
        server - TestLink URL \n
        devKey - Developer Key (Personal API access key)\n
        testplanID - Test plan ID
        """
        self.server = xmlrpclib.Server(server)
        self.devKey = devKey
        self.testplanID = testplanID

    def reportTCResult(self, tcid, buildid, status, testRunNotes=None):
        """
        Сохранение результата выполнения тест-кейса в TestLink
        
        *Args:*\n
        tcid: Test Case ID\n
        buildid: Build ID\n
        status: test case result ("p" - PASS, "f" - FAIL)\n
        testRunNotes: test case notes
        
        *Returns:*\n
        TestLink answer
        """
        data = {"devKey":self.devKey, "testcaseexternalid":tcid, "testplanid":self.testplanID, "buildid":buildid, "status":status, "notes":testRunNotes}
        answer = self.server.tl.reportTCResult(data)
        out = answer[0]
        if out['message'] != 'Success!':
            raise AssertionError('Error in testlink answer. ErrorMessage:'+out['message']+' ErrorCode='+str(out['code']))
        return answer

    def getInfo(self):
        """
        Получение информации с сервера
        """
        return self.server.tl.about()

    def getTestPlanIdByName(self, testProjectName, testPlanName):
        """
        Получение ID тестплана по его имени
        """
        data = {"devKey": self.devKey,
                "testprojectname": testProjectName,
                "testplanname": testPlanName}
        answer = self.server.tl.getTestPlanByName(data)
        out = answer[0]
        testlpanid = out ['id']
        return    testlpanid
    
    def createTestCase(self, testProjectId,testSuiteId,testCaseName,summary,authorlogin,steps=''):
        """
        Создание нового тесткейса
        """
        data = {"devKey": self.devKey,
                "testprojectid": testProjectId,
                "testsuiteid": testSuiteId,
                "testcasename":testCaseName,
                "summary":summary,
                "authorlogin":authorlogin}
        data['actiononduplicatedname'] = 'block'
        data['checkduplicatedname'] = 'true'
        data['steps'] = steps
        answer = self.server.tl.createTestCase(data)
        out = answer[0]
        logger.debug (out)
        testcaseid = out ['id']
        return    testcaseid

    def getProjectIdByName(self, projectName):
        """
        Получение ID проекта по его имени
        """
        data = {
            'devKey': self.devKey
        }
        for tmp_project in self.server.tl.getProjects(data):
            if (tmp_project['name'] == projectName):
                return tmp_project['id']
        return False

    def getTestCaseInternalIdByName(self, testCaseName):
        """
        Получение внутреннего ID тесткейса по его имени
        """
        tc_byname = {
            "devKey": self.devKey,
            "testcasename": testCaseName
        }

        answer = self.server.tl.getTestCaseIDByName(tc_byname)
        out = answer[0]
        if not 'id' in answer[0]:
            raise AssertionError("Test Case not found")
        return    out['id']

    def createBuild(self, buildName, buildNotes):
        """
        Создание билда
        """
        data = {"devKey":self.devKey, "testplanid":self.testplanID, "buildname":buildName, "buildnotes":buildNotes}
        print "Build Name "+buildName + "created with notes" + buildNotes
        x = self.server.tl.createBuild(data)
        out = x[0]
        buildID = out['id']
        print "Build ID is %s" % buildID
        return (buildID)

    def getTestCaseIDFromTestName(self, testcaseName):
        """
        Получение идентификатора тест-кейса в TestLink из имени теста в RobotFramework
        
        *Returns:*\n
        TestCase ID
        
        *Example:*\n
        Имя теста: TEST-1_test case name\n
        => \n
        Идентификатор теста в TestLink: TEST-1
        """
        x1 = testcaseName.split("-")
        x2 = x1[0]
        x3 = x2.split("_")
        testcaseID = x3[1]
        return (testcaseID)
    
    def getTestCaseIDFromTestTags(self, tags):
        """ 
        Получение идентификатора тест-кейса в TestLink из тега теста в RobotFramework
        
        *Returns:*\n
        TestCase ID
        
        *Example:*\n
        Тег в тесте: [Tags]    testlinkid=TEST-40\n
        =>\n
        Идентификатор теста в TestLink: TEST-40
        """
        match_tag = 'testlinkid'
        for tag in tags:
            match = re.match(match_tag, tag)
            if match : 
                split_tag = tag.split('=')
                testcaseID = split_tag[1]
                return testcaseID

    def getLatestBuildForTestPlan(self):
        """
        Получение последнего билда из тестплана.
        """
        data = {"devKey":self.devKey, "testplanid":self.testplanID}
        existingBuild = self.server.tl.getLatestBuildForTestPlan(data)
        return existingBuild['id']
