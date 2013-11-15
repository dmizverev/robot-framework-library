# -*- coding: utf-8 -*-

from robot.api import logger
from robot.utils import ConnectionCache

try:
    import cx_Oracle
except ImportError,info:
    logger.warn ("Import cx_Oracle Error:",info)
if cx_Oracle.version<'3.0':
    logger.warn ("Very old version of cx_Oracle :",cx_Oracle.version)

class OracleDB(object):
    """
    Библиотека для работы с базой данных Oracle.
    
    == Зависимости ==
    | cx_Oracle | http://cx-oracle.sourceforge.net | version > 3.0 |
    | robot framework | http://robotframework.org |
    """
    
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'

    def __init__(self):
        self._connection = None
        self._cache = ConnectionCache()    # использование кеша Robot Framework для одновременной работы с несколькими соединениями
        
    def connect_to_oracle (self, dbName, dbUserName, dbPassword, alias=None):
        """
        Подключение к Oracle.
        
        *Args:*\n
        _dbName_ - имя базы данных;\n
        _dbUserName_ - имя пользователя;\n
        _dbPassword_ - пароль пользователя;\n
        _alias_ - псевдоним соединения;\n
        
        *Returns:*\n
        Индекс текущего соединения.
        
        *Example:*\n
        | Connect To Oracle  |  rb60db  |  bis  |  password |
        """

        try:
            logger.debug ('Connecting using : dbName=%s, dbUserName=%s, dbPassword=%s ' % (dbName, dbUserName, dbPassword))
            connection_string = '%s/%s@%s' % (dbUserName,dbPassword,dbName)
            self._connection=cx_Oracle.connect(connection_string)
            return self._cache.register(self._connection, alias)
        except cx_Oracle.DatabaseError,info:
            raise Exception ("Logon to oracle  Error:",str(info))
    
    def disconnect_from_oracle(self):
        """
        Закрытие текущего соединения с Oracle.
        
        *Example:*\n
        | Connect To Oracle  |  rb60db  |  bis  |  password |
        | Disconnect From Oracle | 
        """

        self._connection.close()
        
    def close_all_oracle_connections (self):
        """
        Закрытие всех соединений с Oracle.
        
        Данный keyword используется для закрытия всех соединений в том случае, если их было открыто несколько штук.
        Использовать [#Disconnect From Oracle|Disconnect From Oracle] и [#Close All Oracle Connections|Close All Oracle Connections] 
        вместе нельзя.
        
        После выполнения этого keyword индекс, возвращаемый [#Connect To Oracle|Connect To Oracle], начинается с 1.
        
        *Example:*\n
        | Connect To Oracle  |  rb60db  |  bis |   password  |  alias=bis |
        | Connect To Oracle  |  rb60db  |  bis_dcs  |  password  |  alias=bis_dsc |
        | Switch Oracle Connection  |  bis |
        | @{sql_out_bis}=  |  Execute Sql String  |  select SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA') from dual |
        | Switch Oracle Connection  |  bis_dsc |
        | @{sql_out_bis_dsc}=  |  Execute Sql String  |  select SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA') from dual |
        | Close All Oracle Connections |
        """
        
        self._connection = self._cache.close_all()
        
    def switch_oracle_connection(self,index_or_alias):
        """
        Переключение между активными соединениями с Oracle, используя их индекс или псевдоним.
        
        Псевдоним задается в keyword [#Connect To Oracle|Connect To Oracle], который также возвращает индекс соединения.
        
        *Args:*\n
        _index_or_alias_ - индекс соединения или его псевдоним;
        
        *Returns:*\n
        Индекс предыдущего соединения.
        
        *Example:* (switch by alias)\n
        | Connect To Oracle  |  rb60db  |  bis |   password  |  alias=bis |
        | Connect To Oracle  |  rb60db  |  bis_dcs  |  password  |  alias=bis_dsc |
        | Switch Oracle Connection  |  bis |
        | @{sql_out_bis}=  |  Execute Sql String  |  select SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA') from dual |
        | Switch Oracle Connection  |  bis_dsc |
        | @{sql_out_bis_dsc}=  |  Execute Sql String  |  select SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA') from dual |
        | Close All Oracle Connections |
        =>\n
        @{sql_out_bis} = BIS\n
        @{sql_out_bis_dcs}= BIS_DCS
        
        *Example:* (switch by index)\n
        | ${bis_index}=  |  Connect To Oracle  |  rb60db  |  bis  |  password  |
        | ${bis_dcs_index}=  |  Connect To Oracle  |  rb60db  |  bis_dcs  |  password |
        | @{sql_out_bis_dcs_1}=  |  Execute Sql String  |  select SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA') from dual |
        | ${previous_index}=  |  Switch Oracle Connection  |  ${bis_index} |
        | @{sql_out_bis}=  |  Execute Sql String  |  select SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA') from dual |
        | Switch Oracle Connection  |  ${previous_index} |
        | @{sql_out_bis_dcs_2}=  |  Execute Sql String  |  select SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA') from dual |
        | Close All Oracle Connections |
        =>\n
        ${bis_index}= 1\n
        ${bis_dcs_index}= 2\n
        @{sql_out_bis_dcs_1} = BIS_DCS\n
        ${previous_index}= 2\n
        @{sql_out_bis} = BIS\n
        @{sql_out_bis_dcs_2}= BIS_DCS
        """
        
        old_index = self._cache.current_index
        self._connection = self._cache.switch(index_or_alias)
        return old_index
    
    def _execute_sql (self, cursor, Statement):
        logger.debug("Executing :\n %s" % Statement)
        cursor.prepare(Statement)
        return cursor.execute(None)

    def execute_plsql_block (self,plsqlStatement):
        """
        Выполнение PL\SQL блока.
        
        *Args:*\n
        _plsqlStatement_ - PL\SQL блок;\n
        
        *Raises:*\n
        PLSQL Error: Ошибка выполнения PL\SQL; выводится сообщение об ошибке в кодировке той БД, где выполняется код.
        
        *Example:*\n
        | *Settings* | *Value* |
        | Library    |       OracleDB |
        
        | *Variables* | *Value* |
        | ${var_failed}    |       3 |
        
        | *Test Cases* | *Action* | *Argument* | *Argument* | *Argument* |
        | Simple |
        |    | ${statement}=  |  catenate   |   SEPARATOR=\\r\\n  |    DECLARE  |
        |    | ...            |             |                     |       a NUMBER := ${var_failed}; |
        |    | ...            |              |                     |   BEGIN |
        |    | ...            |              |                    |       a := a + 1; |
        |    | ...            |              |                    |        if a = 4 then |
        |    | ...            |              |                    |         raise_application_error ( -20001, 'This is a custom error' ); |
        |    | ...            |              |                    |        end if; |
        |    | ...            |              |                    |     END; |
        |    | Execute Plsql Block   |  ${statement} |
        =>\n
        DatabaseError: ORA-20001: This is a custom error
        """

        cursor = None
        try:
            cursor = self._connection.cursor()
            self._execute_sql (cursor,plsqlStatement)
            self._connection.commit()
        finally:
            if cursor:
                self._connection.rollback()
    
    def execute_plsql_block_with_dbms_output (self,plsqlStatement):
        """
        Выполнение PL\SQL блока с dbms_output().
        
        *Args:*\n
        _plsqlStatement_ - PL\SQL блок;\n
        
        *Raises:*\n
        PLSQL Error: Ошибка выполнения PL\SQL; выводится сообщение об ошибке в кодировке той БД, где выполняется код.
        
        *Returns:*\n
        Список с значениями из функций Oracle dbms_output.put_line().
        
        *Example:*\n
        | *Settings* | *Value* |
        | Library    |       OracleDB |
        
        | *Variables* | *Value* |
        | ${var}    |       4 |
        
        | *Test Cases* | *Action* | *Argument* | *Argument* | *Argument* |
        | Simple |
        |    | ${statement}=  |  catenate   |   SEPARATOR=\\r\\n  |    DECLARE  |
        |    | ...            |             |                     |       a NUMBER := ${var}; |
        |    | ...            |              |                     |   BEGIN |
        |    | ...            |              |                    |       a := a + 1; |
        |    | ...            |              |                    |        if a = 4 then |
        |    | ...            |              |                    |         raise_application_error ( -20001, 'This is a custom error' ); |
        |    | ...            |              |                    |        end if; |
        |    | ...            |              |                    |        dbms_output.put_line ('text '||a||', e-mail text'); |
        |    | ...            |              |                    |        dbms_output.put_line ('string 2 '); |
        |    | ...            |              |                    |     END; |
        |    | @{dbms}=       | Execute Plsql Block With Dbms Output   |  ${statement} |
        =>\n
        | @{dbms} | text 5, e-mail text |
        | | string 2 |
        """

        cursor = None
        dbms_output = []
        try:
            cursor = self._connection.cursor()
            cursor.callproc("dbms_output.enable")
            self._execute_sql (cursor,plsqlStatement)
            self._connection.commit()
            statusVar = cursor.var(cx_Oracle.NUMBER)
            lineVar = cursor.var(cx_Oracle.STRING)
            while True:
                cursor.callproc("dbms_output.get_line", (lineVar, statusVar))
                if statusVar.getvalue() != 0:
                    break
                dbms_output.append(lineVar.getvalue())
            return dbms_output
        finally:
            if cursor:
                self._connection.rollback()

    def execute_sql_string (self,plsqlStatement):
        """
        Выполнение SQL выборки из БД.
        
        *Args:*\n
        _plsqlStatement_ - PL\SQL блок;\n
        
        *Raises:*\n
        PLSQL Error: Ошибка выполнения PL\SQL; выводится сообщение об ошибке в кодировке той БД, где выполняется код.
        
        *Returns:*\n
        Выборка в виде таблицы.
        
        *Example:*\n
        | @{query}= | Execute Sql String | select sysdate, sysdate+1 from dual | 
        | Set Test Variable  |  ${sys_date}  |  ${query[0][0]} | 
        | Set Test Variable  |  ${next_date}  |  ${query[0][1]} | 
        """

        cursor = None
        try:
            cursor = self._connection.cursor()
            self._execute_sql (cursor,plsqlStatement)
            return cursor.fetchall()
        finally:
            if cursor:
                self._connection.rollback()
