# -*- coding: utf-8 -*-

from robot.api import logger
from robot.utils import ConnectionCache
import httplib
import base64 
import json
import socket
import urlparse
import urllib


class RabbitMqManager(object):
    """
    Библиотека для управления сервером RabbitMq.
    
    Реализована на основе:
    - [ http://hg.rabbitmq.com/rabbitmq-management/raw-file/3646dee55e02/priv/www-api/help.html | RabbitMQ Management HTTP API ]
    - [ https://github.com/rabbitmq/rabbitmq-management/blob/master/bin/rabbitmqadmin | rabbitmqadmin ]
    
    == Зависимости ==
    | robot framework | http://robotframework.org |
    
    == Example ==
    | *Settings* | *Value* |
    | Library    |       RabbitMqManager |
    | Library     |      Collections |
    
    | *Test Cases* | *Action* | *Argument* | *Argument* | *Argument* | *Argument* | *Argument* |
    | Simple |
    |    | Connect To Rabbitmq | my_host_name | 15672 | guest | guest | alias=rmq |
    |    | ${overview}= | Overview |
    |    | Log Dictionary | ${overview} |
    |    | Close All Rabbitmq Connections |
    """

    ROBOT_LIBRARY_SCOPE='GLOBAL'

    def __init__(self):
        self._connection=None
        self.headers=None
        self._cache=ConnectionCache()

    def connect_to_rabbitmq (self, host, port, username = 'guest', password = 'guest', timeout = 15, alias = None):
        """
        Подключение к серверу RabbitMq.
        
        *Args:*\n
        _host_ - имя сервера;\n
        _port_ - номер порта;\n
        _username_ - имя пользователя;\n
        _password_ - пароль пользователя;\n
        _timeout_ - время ожидания соединения;\n
        _alias_ - псевдоним соединения;\n 
        
        *Returns:*\n
        Индекс текущего соединения.
        
        *Raises:*\n
        socket.error в том случае, если невозможно создать соединение.
        
        *Example:*\n
        | Connect To Rabbitmq | my_host_name | 15672 | guest | guest | alias=rmq |
        """

        port=int (port)
        timeout=int (timeout)
        logger.debug ('Connecting using : host=%s, port=%d, username=%s, password=%s, timeout=%d, alias=%s '%(host, port, username, password, timeout, alias))
        self.headers={"Authorization":"Basic "+base64.b64encode(username+":"+password)}
        try:
            self._connection=httplib.HTTPConnection (host, port, timeout)
            self._connection.connect()
            return self._cache.register(self._connection, alias)
        except socket.error, e:
            raise Exception ("Could not connect to RabbitMq", str(e))

    def switch_rabbitmq_connection (self, index_or_alias):
        """
        Переключение между активными соединениями с RabbitMq, используя их индекс или псевдоним.
        
        Псевдоним задается в keyword [#Connect To Rabbitmq|Connect To Rabbitmq], который также возвращает индекс соединения.
        
        *Args:*\n
        _index_or_alias_ -индекс соединения или его псевдоним;
        
        *Returns:*\n
        Индекс предыдущего соединения.
        
        *Example:*\n
        | Connect To Rabbitmq | my_host_name_1 | 15672 | guest | guest | alias=rmq1 |
        | Connect To Rabbitmq | my_host_name_2 | 15672 | guest | guest | alias=rmq2 |
        | Switch Rabbitmq Connection | rmq1 |
        | ${live}= | Is alive |
        | Switch Rabbitmq Connection | rmq2 |
        | ${live}= | Is alive |
        | Close All Rabbitmq Connections |
        """

        old_index=self._cache.current_index
        self._connection=self._cache.switch(index_or_alias)
        return old_index

    def disconnect_from_rabbitmq(self):
        """
        Закрытие текущего соединения с RabbitMq.
        
        *Example:*\n
        | Connect To Rabbitmq | my_host_name | 15672 | guest | guest | alias=rmq |
        | Disconnect From Rabbitmq |
        """

        logger.debug ('Close connection with : host=%s, port=%d  '%(self._connection.host, self._connection.port))
        self._connection.close()

    def close_all_rabbitmq_connections (self):
        """
        Закрытие всех соединений с RabbitMq.
        
        Данный keyword используется для закрытия всех соединений в том случае, если их было открыто несколько штук.
        Использовать [#Disconnect From Rabbitmq|Disconnect From Rabbitmq] и [#Close All Rabbitmq Connections|Close All Rabbitmq Connections] 
        вместе нельзя.
        
        После выполнения этого keyword индекс, возвращаемый [#Connect To Rabbitmq|Connect To Rabbitmq], начинается с 1.
        
        *Example:*\n
        | Connect To Rabbitmq | my_host_name | 15672 | guest | guest | alias=rmq |
        | Close All Rabbitmq Connections |
        """

        self._connection=self._cache.close_all()

    def _http_request (self, method, path, body):
        """
        Выполнение запросов к RabbitMq
        
        *Args:*\n
        _method_ - метод запроса;\n
        _path_ - uri запроса;\n
        _body_ - тело POST-запроса;\n
        """

        if body!="":
            self.headers["Content-Type"]="application/json"

        logger.debug ('Prepared request with metod '+method+' to '+'http://'+self._connection.host+':'+str(self._connection.port)+path+' and body\n'+body)

        try:
            self._connection.request(method, path, body, self.headers)
        except socket.error, e:
            raise Exception("Could not send request: {0}".format(e))

        resp=self._connection.getresponse()

        if resp.status==400:
            raise Exception (json.loads(resp.read())['reason'])
        if resp.status==401:
            raise Exception("Access refused: {0}".format('http://'+self._connection.host+':'+str(self._connection.port)+path))
        if resp.status==404:
            raise Exception("Not found: {0}".format('http://'+self._connection.host+':'+str(self._connection.port)+path))
        if resp.status==301:
            url=urlparse.urlparse(resp.getheader('location'))
            [host, port]=url.netloc.split(':')
            self.options.hostname=host
            self.options.port=int(port)
            return self.http(method, url.path+'?'+url.query, body)
        if resp.status<200 or resp.status>400:
            raise Exception("Received %d %s for request %s\n%s"
                            %(resp.status, resp.reason, 'http://'+self._connection.host+':'+str(self._connection.port)+path, resp.read()))
        return resp.read()

    def _get (self, path):
        return self._http_request('GET', '/api%s'%path, '')

    def _put (self, path, body):
        return self._http_request("PUT", "/api%s"%path, body)

    def _post (self, path, body):
        return self._http_request("POST", "/api%s"%path, body)

    def _delete (self, path):
        return self._http_request("DELETE", "/api%s"%path, "")

    def _quote_vhost (self, vhost):
        """
        Декодирование vhost.
        """

        if vhost=='/':
            vhost='%2F'
        if vhost!='%2F':
            vhost=urllib.quote(vhost)
        return vhost

    def is_alive(self):
        """
        Проверка работоспособности RabbitMq.
        
        Отправляется GET-запрос следующего вида: 'http://<host>:<port>/api/' и проверяется код возврата.
        
        *Returns:*\n
        bool True, если код возврата равен 200.\n
        bool False во всех остальных случаях.
        
        *Raises:*\n
        socket.error в том случае, если невозмодно отправить GET-запрос.
        
        *Example:*\n
        | ${live}=  |  Is Alive |
        =>\n
        True
        """

        try:
            self._connection.request('GET', '/api/')
        except socket.error, e:
            raise Exception("Could not send request: {0}".format(e))
        resp=self._connection.getresponse()
        resp.read()
        logger.debug ('Response status=%d'%resp.status)
        if resp.status==200 :
            return True
        else:
            return False

    def overview (self):
        """
        Информация о сервере RabbitMq.
        
        *Returns:*\n
        Словарь с информацией о сервере.
        
        *Example:*\n
        | ${overview}=  |  Overview |
        | Log Dictionary  |  ${overview} |
        | ${version}=  |  Get From Dictionary | ${overview}  |  rabbitmq_version |
        =>\n
        Dictionary size is 13 and it contains following items:
        | erlang_full_version | Erlang R16B02 (erts-5.10.3) [source] [64-bit] [smp:2:2] [async-threads:30] [hipe] [kernel-poll:true] |
        | erlang_version | R16B02 |
        | listeners | [{u'node': u'rabbit@srv2-rs582b-m', u'ip_address': u'0.0.0.0', u'protocol': u'amqp', u'port': 5672}] |
        | management_version | 3.1.0 |
        | message_stats | [] |
        
        ${version} = 3.1.0
        """

        return json.loads(self._get ('/overview'))

    def connections (self):
        """
        Список открытых соединений.
        """

        return json.loads(self._get ('/connections'))

    def get_name_of_all_connections (self):
        """
        Список имен всех открытых соединений.
        """
        
        names=[]
        data=self.connections ()
        for item in data :
            names.append(item['name'])
        return names
    
    def channels (self):
        """
        Список открытых каналов.
        """

        return json.loads(self._get ('/channels'))

    def exchanges (self):
        """
        Список exchange.
        
        *Example:*\n
        | ${exchanges}=  |  Exchanges |
        | Log List  |  ${exchanges} |
        | ${item}=  |  Get From list  |  ${exchanges}  |  1 |
        | ${name}=  |  Get From Dictionary  |  ${q}  |  name  |
        =>\n
        List length is 8 and it contains following items:
        | 0 | {u'name': u'', u'durable': True, u'vhost': u'/', u'internal': False, u'message_stats': [], u'arguments': {}, u'type': u'direct', u'auto_delete': False} |
        | 1 | {u'name': u'amq.direct', u'durable': True, u'vhost': u'/', u'internal': False, u'message_stats': [], u'arguments': {}, u'type': u'direct', u'auto_delete': False} |
        ...\n
        ${name} = amq.direct
        """

        return json.loads(self._get ('/exchanges'))

    def get_names_of_all_exchanges (self):
        """
        Список имён всех exchanges.
        
        *Example:*\n
        | ${names}=  |  Get Names Of All Exchanges |
        | Log List  |  ${names} |
        =>\n
        | List has one item:
        | amq.direct
        """
        
        names=[]
        data=self.exchanges ()
        for item in data :
            names.append(item['name'])
        return names

    def queues (self):
        """
        Список очередей.
        """

        return json.loads(self._get ('/queues'))

    def get_queues_on_vhost (self, vhost = '%2F'):
        """
        Список очередей для виртуального хоста.
        
        *Args:*\n
        _vhost_ -имя виртуального хоста (перекодируется при помощи urllib.quote);
        """

        return json.loads(self._get ('/queues/'+self._quote_vhost(vhost)))

    def get_names_of_queues_on_vhost (self, vhost = '%2F'):
        """
        Список имен очередей виртуального хоста.
        
        *Args:*\n
        - vhost: имя виртуального хоста (перекодируется при помощи urllib.quote)
        
        *Example:*\n
        | ${names}=  |  Get Names Of Queues On Vhost |
        | Log List  |  ${names} |
        =>\n
        | List has one item:
        | federation: ex2 -> rabbit@server.net.ru
        """
        names=[]
        data=self.get_queues_on_vhost (vhost)
        for item in data :
            names.append(item['name'])
        return names
    
    def queue_exists(self, queue, vhost='%2F'):
        """
        Verifies that the one or more queues exists
        """
        names = self.get_names_of_queues_on_vhost()
        if queue in names:
            return True
        else:
            return False

    def delete_queues_by_name (self, name, vhost = '%2F'):
        """
        Удаление очереди с виртуального хоста.
        
        *Args:*\n
        _name_ - имя очереди (перекодируется urllib.quote);\n
        _vhost_ - имя виртуального хоста (перекодируется urllib.quote);\n
        """

        return self._delete('/queues/'+self._quote_vhost(vhost)+'/'+urllib.quote(name))

    def vhosts (self):
        """
        Список виртуальных хостов.
        """

        return json.loads(self._get ('/vhosts'))

    
    def nodes(self):
        """
        List of nodes in the RabbitMQ cluster
        """
        return json.loads(self._get('/nodes'))

    @property
    def _cluster_name(self):
        """
        Name identifying this RabbitMQ cluster.
        """
        return json.loads(self._get('/cluster-name'))

    def create_queues_by_name(self, name, auto_delete=False, durable=True, arguments={}, vhost='%2F'):
        """
        Create an individual queue.
        """
        node = self._cluster_name['name']
        body = json.dumps({
            "auto_delete": auto_delete,
            "durable": durable,
            "arguments": arguments,
            "node": node
        })
        return self._put('/queues/' + self._quote_vhost(vhost) + '/' + urllib.quote(name), body=body)

    def publish_message_by_name(self, queue, msg, properties, vhost='%2F'):
        """
        Publish a message to a given exchange
        """

        name = "amq.default"
        body = json.dumps({
            "properties": properties,
            "routing_key": queue,
            "payload": msg,
            "payload_encoding": "string"
        })
        routed = self._post('/exchanges/' + self._quote_vhost(vhost) +
                            '/' + urllib.quote(name) + '/publish', body=body)
        return json.loads(routed)

    def get_messages_by_queue(self, queue, count=5, requeue=False, encoding="auto", truncate=50000, vhost='%2F'):
        """
        Get messages from a queue.
        """

        body = json.dumps({
            "count": count,
            "requeue": requeue,
            "encoding": encoding,
            "truncate": truncate
        })
        messages = self._post('/queues/' + self._quote_vhost(vhost) +
                              '/' + urllib.quote(queue) + '/get', body=body)
        return json.loads(messages)
    
    def purge_messages_by_queue(self, name, vhost='%2F'):
        """
        Purge contents of a queue.
        """
        return self._delete('/queues/' + self._quote_vhost(vhost) + '/' + urllib.quote(name) + '/contents')

