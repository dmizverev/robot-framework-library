# -*- coding: utf-8 -*-

from robot.api import logger
from robot.utils import ConnectionCache
import winrm

class WinRMLibrary(object):
    """
    Robot Framework library for Windows Remote Management, based on pywinrm.
    
    == Enable Windows Remote Shell ==
    - [ http://support.microsoft.com/kb/555966 | KB-555966 ]
    - Execute on windows server:
     
     | winrm set winrm/config/client/auth @{Basic="true"}
     | winrm set winrm/config/service/auth @{Basic="true"}
     | winrm set winrm/config/service @{AllowUnencrypted="true"}

    == Dependence ==
    | pywinrm | https://pypi.python.org/pypi/pywinrm | 
    | robot framework | http://robotframework.org |
    """

    ROBOT_LIBRARY_SCOPE='GLOBAL'

    def __init__(self):
        self._session=None
        self._cache=ConnectionCache('No sessions created')

    def create_session (self, alias, hostname, login, password):
        """
        Create session with windows host. 
        
        Does not support domain authentification.
        
        *Args:*\n
        _alias_ - robot framework alias to identify the session\n
        _hostname_ -  windows hostname (not IP)\n
        _login_ - windows local login\n
        _password_ - windows local password
        
        *Returns:*\n
        Session index
        
        *Example:*\n
        | Create Session  |  server  |  windows-host |  Administrator  |  1234567890 |
        """

        logger.debug ('Connecting using : hostname=%s, login=%s, password=%s '%(hostname, login, password))
        self._session=winrm.Session(hostname, (login, password))
        return self._cache.register(self._session, alias)

    def run_cmd (self, alias, command, params=None):
        """
        Execute command on remote mashine.
        
        *Args:*\n
        _alias_ - robot framework alias to identify the session\n
        _command_ -  windows command\n
        _params_ - lists of command's parameters
        
        *Returns:*\n
        Result object with methods: status_code, std_out, std_err.
        
        *Example:*\n
        | ${params}=  | Create List  |  "/all" |
        | ${result}=  |  Run cmd  |  server  |  ipconfig  |  ${params} |
        | Log  |  ${result.status_code} |
        | Log  |  ${result.std_out} |
        | Log  |  ${result.std_err} |
        =>\n
        | 0 
        | Windows IP Configuration
        |    Host Name . . . . . . . . . . . . : WINDOWS-HOST
        |    Primary Dns Suffix  . . . . . . . :
        |    Node Type . . . . . . . . . . . . : Hybrid
        |    IP Routing Enabled. . . . . . . . : No
        |    WINS Proxy Enabled. . . . . . . . : No
        | 
        """

        if params is not None:
            log_cmd=command+' '+' '.join(params)
        else:
            log_cmd=command
        logger.info ('Run command on server with alias "%s": %s '%(alias, log_cmd))
        self._session=self._cache.switch(alias)
        result=self._session.run_cmd (command, params)
        return result

    def run_ps (self, alias, script):
        """
        Run power shell script on remote mashine.
        
        *Args:*\n
         _alias_ - robot framework alias to identify the session\n
         _script_ -  power shell script\n
        
        *Returns:*\n
         Result object with methods: status_code, std_out, std_err.
        
        *Example:*\n
        
        | ${result}=  |  Run ps  |  server  |  get-process iexplore|select -exp ws|measure-object -sum|select -exp Sum |
        | Log  |  ${result.status_code} |
        | Log  |  ${result.std_out} |
        | Log  |  ${result.std_err} |
        =>\n
        | 0                         
        | 56987648                         
        |              
        """

        logger.info ('Run power shell script on server with alias "%s": %s '%(alias, script))
        self._session=self._cache.switch(alias)
        result=self._session.run_ps (script)
        return result

    def delete_all_sessions(self):
        """ Removes all sessions with windows hosts"""

        self._cache.empty_cache()