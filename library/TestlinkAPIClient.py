# -*- coding: utf-8 -*-
import xmlrpclib
import re
from robot.api import logger

class TestlinkAPIClient(object):
    """
    Реализация REST XML-API взаимодействия с [ http://testlink.org/ | TestLink ].
    
    Реализована на основе:
    - [ http://jetmore.org/john/misc/phpdoc-testlink193-api/TestlinkAPI/TestlinkXMLRPCServer.html | API TestLink ]
    """

    def __init__(self, server, devKey, testplanID = None):
        """
        *Args:*\n
        _server_ - url к Testlink API;\n
        _devKey_ - Testlink Developer Key;\n
        _testplanID_ - ID тестплана; 
        """

        self.server=xmlrpclib.Server(server)
        self.devKey=devKey
        self.testplanID=testplanID

    def reportTCResult(self, tcid, buildid, status, testRunNotes = None):
        """
        Сохранение результата выполнения тест-кейса в TestLink.
        
        *Args:*\n
        _tcid_ - ID тесткейса;\n
        _buildid_ - ID билда;\n
        _status_ - результат выполнения тесткейса ("p" - PASS, "f" - FAIL);\n
        _testRunNotes_ - примечание к выполенению тесткейса;
        
        *Returns:*\n
        Ответ от Testlink с информацией о завершении операции.
        """

        data={"devKey":self.devKey, "testcaseexternalid":tcid, "testplanid":self.testplanID, "buildid":buildid, "status":status, "notes":testRunNotes}
        answer=self.server.tl.reportTCResult(data)
        out=answer[0]
        if out['message']!='Success!':
            raise AssertionError('Error in testlink answer. ErrorMessage:'+out['message']+' ErrorCode='+str(out['code']))
        return answer

    def getInfo(self):
        """
        Получение информации с сервера.
        
        *Returns:*\n
        Информация о Testlink.
        
        *Example:*\n
        Testlink API Version: 1.0 initially written by Asiel Brumfield\n
        with contributions by TestLink development Team
        """

        return self.server.tl.about()

    def getTestPlanIdByName(self, testProjectName, testPlanName):
        """
        Получение ID тестплана по его имени.
        
        *Args:*\n
        _testProjectName_ - имя проекта, в котором находятся тесты;\n
        _testPlanName_ - имя тестплана, в котором находятся тесты;\n
        
        *Returns:*\n
        ID тестплана.
        """

        data={"devKey": self.devKey,
                "testprojectname": testProjectName,
                "testplanname": testPlanName}
        answer=self.server.tl.getTestPlanByName(data)
        out=answer[0]
        testlpanid=out ['id']
        return    testlpanid

    def createTestCase(self, testProjectId, testSuiteId, testCaseName, summary, authorlogin, steps = ''):
        """
        Создание нового тесткейса.
        
        *Args:*\n
        _testProjectId_ - ID проекта, в который необходимо добавить тесткейс;\n
        _testSuiteId_ - ID тестсьюты, в которую необходимо добавить тесткейс;\n
        _testCaseName_ - имя тесткейса;\n
        _summary_ - описание тесткейса;\n
        _authorlogin_ - имя пользователя, от которого создаётся тесткейс;\n
        _steps_ - шаги выполнения тесткейса;
        
        *Returns:*\n
        ID созданного тесткейса.
        """

        data={"devKey": self.devKey,
                "testprojectid": testProjectId,
                "testsuiteid": testSuiteId,
                "testcasename":testCaseName,
                "summary":summary,
                "authorlogin":authorlogin}
        data['actiononduplicatedname']='block'
        data['checkduplicatedname']='true'
        data['steps']=steps
        answer=self.server.tl.createTestCase(data)
        out=answer[0]
        logger.debug (out)
        testcaseid=out ['id']
        return    testcaseid

    def getProjectIdByName(self, projectName):
        """
        Получение ID проекта по его имени.
        
        *Args:*\n
        _projectName_ - имя проекта;
        
        *Returns:*\n
        ID проекта.\n
        False в случае неудачи.
        """

        data={
            'devKey': self.devKey
        }
        for tmp_project in self.server.tl.getProjects(data):
            if (tmp_project['name']==projectName):
                return tmp_project['id']
        return False

    def getTestCaseInternalIdByName(self, testCaseName):
        """
        Получение внутреннего ID тесткейса по его имени.\n
        Тесткейсы в Testlink имеют внутренние ID и внешние.
        
        *Args:*\n
        _testCaseName_ - имя тесткейса;\n
        
        *Returns:*\n
        ID тесткейса.
        
        *Raises:*\n
        "Test Case not found" в том случе, если тесткейс не найден.
        """

        tc_byname={
            "devKey": self.devKey,
            "testcasename": testCaseName
        }

        answer=self.server.tl.getTestCaseIDByName(tc_byname)
        out=answer[0]
        if not 'id' in answer[0]:
            raise AssertionError("Test Case not found")
        return    out['id']

    def createBuild(self, buildName, buildNotes):
        """
        Создание билда.
        
        *Args:*\n
        _buildName_ - имя создаваемого билда;\n
        _buildNotes_ - примечание к создаваемому билду;
        
        *Returns:*\n
        ID созданного билда.
        """

        data={"devKey":self.devKey, "testplanid":self.testplanID, "buildname":buildName, "buildnotes":buildNotes}
        print "Build Name "+buildName+"created with notes"+buildNotes
        x=self.server.tl.createBuild(data)
        out=x[0]
        buildID=out['id']
        print "Build ID is %s"%buildID
        return (buildID)

    def getTestCaseIDFromTestName(self, testcaseName):
        """
        Получение идентификатора тесткейса для TestLink из его имени в Robot Framework.
        Имя тесткейса в Robot Framework должно быть вида: <id>_<test name>
        
        *Args:*\n
        _testcaseName_ - имя тесткейса в Robot Framework;\n
        
        *Returns:*\n
        ID тесткейса для Testlink из его имени.
        
        *Example:*\n
        Имя тесткейса в Robot Framework: TEST-1_test case name\n
        => \n
        Идентификатор теста для TestLink: TEST-1
        """

        x1=testcaseName.split("-")
        x2=x1[0]
        x3=x2.split("_")
        testcaseID=x3[1]
        return (testcaseID)

    def getTestCaseIDFromTestTags(self, tags):
        """ 
        Получение идентификатора тесткейса для TestLink из тега теста в Robot Framework.
        Один из тегов в списке должен быть вида testlinkid=<id>
        
        *Args:*\n
        _tags_ - список тегов для тесткейса в Robot Framework;\n
        
        *Returns:*\n
        ID тесткейса для Testlink из его тегов.
        
        *Example:*\n
        Тег в тесте: [Tags]    testlinkid=TEST-40\n
        =>\n
        Идентификатор теста в TestLink: TEST-40
        """

        match_tag='testlinkid'
        for tag in tags:
            match=re.match(match_tag, tag)
            if match :
                split_tag=tag.split('=')
                testcaseID=split_tag[1]
                return testcaseID

    def getLatestBuildForTestPlan(self):
        """
        Получение последнего билда из тестплана.
        
        *Returns:*\n
        ID билда.
        """

        data={"devKey":self.devKey, "testplanid":self.testplanID}
        existingBuild=self.server.tl.getLatestBuildForTestPlan(data)
        return existingBuild['id']
