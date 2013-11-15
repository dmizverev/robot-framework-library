# -*- coding: utf-8 -*-

from robot.libraries.BuiltIn import BuiltIn
from robot.libraries.OperatingSystem import OperatingSystem
import os

class AdvancedLogging(object):
    """
    Creating additional logs when testing.
    If during the test you want to add any additional information in the file, then this library
    provide a hierarchy of folders and files for logging.
    Folder hierarchy is created as follows: output_dir/test_log_folder_name/Test_Suite/Test_Suite/Test_Case/file.log
    Log files and folders are not removed before the test, and overwritten of new files.
    
     == Dependency: ==
    | robot framework | http://robotframework.org |
    -------
    
    When initializing the library, you can define two optional arguments
    | *Argument Name*      |  *Default value*  | *Description*                                                 |
    | output_dir           |  ${OUTPUT_DIR}    | The directory in which create the folder with additional logs |
    | test_log_folder_name |  Advanced_Logs    | Name of the folder from which to build a hierarchy of logs    |
    -------
    
    == Example: ==
    | *Settings*  |  *Value*           | *Value*  |  *Value*        |
    | Library     |  AdvancedLogging   | C:/Temp  |   LogFromServer |
    | Library     |  SSHLibrary        |          |                 |
    
    | *Test cases*              | *Action*                  | *Argument*             |  *Argument*            |
    | Example_TestCase          | ${out}=                   | Execute Command        |  grep error output.log |
    |                           | Write advanced testlog    | error.log              |  ${out}                |
    =>\n
    File C:/Temp/LogFromServer/TestSuite name/Example_TestCase/error.log  with content from variable ${out}
    """

    ROBOT_LIBRARY_SCOPE='TEST SUITE'

    def __init__(self, output_dir = None, test_log_folder_name = 'Advanced_Logs'):
        self.os=OperatingSystem()
        self.bi=BuiltIn()

        self.output_dir=output_dir
        self.test_log_folder_name=test_log_folder_name
        self.sep='/'

    @property
    def _suite_folder (self):
        """
        Define variables that are initialized by a call 'TestSuite'
        """


        if self.output_dir==None :
            self.output_dir=self.bi.get_variable_value('${OUTPUT_DIR}')

        suite_name=self.bi.get_variable_value('${SUITE_NAME}')
        suite_name=suite_name.replace('.', self.sep)
        self.output_dir=os.path.normpath(self.output_dir)
        self.test_log_folder_name=os.path.normpath(self.test_log_folder_name)

        suite_folder=self.output_dir+self.sep+self.test_log_folder_name+self.sep+suite_name
        return os.path.normpath(suite_folder)

    def Write_Advanced_Testlog (self, filename, content):
        """ 
        Inclusion content in additional log file
        
        Return: path to filename
        
        Example:
        | Write advanced testlog   | log_for_test.log  |  test message |
        =>\n
        File ${OUTPUT_DIR}/Advanced_Logs/<TestSuite name>/<TestCase name>/log_for_test.log with content 'test message'
        """

        test_name=BuiltIn().get_variable_value('${TEST_NAME}')

        if not test_name:
            log_folder=self._suite_folder+self.sep
        else:
            log_folder=self._suite_folder+self.sep+test_name

        self.os.create_file(log_folder+self.sep+filename, content)

        return os.path.normpath(log_folder+self.sep+filename)

    def Create_Advanced_Logdir (self):
        """  
        Creating a folder hierarchy for TestSuite
        
        Return: path to folder
        
        Example:
        | *Settings* | *Value* |
        | Library    |        AdvancedLogging |
        | Library    |       OperatingSystem |
        
        | *Test Cases* | *Action* | *Argument* |
        | ${ADV_LOGS_DIR}=   | Create advanced logdir            |                |
        | Create file        | ${ADV_LOGS_DIR}/log_for_suite.log |   test message |
        =>\n
        File ${OUTPUT_DIR}/Advanced_Logs/<TestSuite name>/log_for_suite.log with content 'test message'
        """

        test_name=self.bi.get_variable_value('${TEST_NAME}')

        if not test_name:
            log_folder=self._suite_folder+self.sep
        else:
            log_folder=self._suite_folder+self.sep+test_name

        self.os.create_directory(os.path.normpath(log_folder))

        return os.path.normpath(log_folder)
