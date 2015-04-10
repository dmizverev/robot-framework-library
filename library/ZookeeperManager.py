# -*- coding: utf-8 -*-
from robot.libraries.BuiltIn import BuiltIn
from kazoo.client import KazooClient
from kazoo.exceptions import NoNodeError

class ZookeeperManager(object):
    """
    Working with Apache Zookeeper.
    Based on Kazoo (Python library). All errors described in "Returns" section are kazoo exceptions (kazoo.exceptions).

    == Notice ==
    kazoo library work only on Linux now
    
    == Dependence ==
    | robot framework   | http://robotframework.org           |
    | kazoo             | https://github.com/python-zk/kazoo  |
    """

    ROBOT_LIBRARY_SCOPE='GLOBAL'

    def __init__(self):
        self.bi = BuiltIn()

    def connect_to_zookeeper(self, hosts, timeout=10):
        """
        Connecting to Zookeeper

        *Args:*\n
        _host_ - comma-separated list of hosts to connect.\n
        _timeout_ - connection timeout in seconds. Default timeout is 10 seconds.\n

        *Example:*\n
        | Connect To Zookeeper | host1:2181, host2 | 25 |
        """
        self.zk = KazooClient(hosts, timeout)
        self.zk.start()

    def disconnect_from_zookeeper(self):
        """
        Close all connections to Zookeeper

        *Example:*\n
        | Connect To Zookeeper | 127.0.0.1: 2181 |
        | Disconnect From Zookeeper |
        """
        self.zk.stop()
        self.zk.close()

    def create_node(self, path, value='', force=False):
        """
        Create a node with a value.

        *Args:*\n
        _path_ - node path.\n
        _value_ - node value. Default is an empty string.\n
        _force_ - if TRUE parent path will be created. Default value is FALSE.\n

        *Raises:*\n
        _NodeExistError_ - node already exists.\n
        _NoNodeError_ - parent node doesn't exist.\n
        _NoChildrenForEphemeralsError_ - parent node is an ephemeral mode.\n
        _ZookeeperError_ - value is too large or server returns a non-zero error code.\n
        
        *Example:*\n
        | Create Node  |  /my/favorite/node  |  my_value |  ${TRUE} |
        """
        string_value = value.encode('utf-8')
        self.zk.create(path, string_value, None, False, False, force)

    def delete_node(self, path, force=False):
        """
        Delete a node.

        *Args:*\n
        _path_ - node path.\n
        _force_ - if TRUE and node exists - recursively delete a node with all its children, 
                  if TRUE and node doesn't exists - error won't be raised. Default value is FALSE.

        *Raises:*\n
        _NoNodeError_ - node doesn't exist.\n
        _NotEmptyError_ - node has children.\n
        _ZookeeperError_ - server returns a non-zero error code.
        """
        try:
            self.zk.delete(path, -1, force)
        except NoNodeError:
            if (force):
                pass
            else:
                raise

    def exists(self, path):
        """
        Check is a node exists.

        *Args:*\n
        _path_ - node path.

        *Returns:*\n
        TRUE if a node exists, FALSE in other way.
        """
        node_stat = self.zk.exists(path)
        if (node_stat != None):
            #Node exists
            return True
        else:
            #Node doesn't exist
            return False

    def set_value(self, path, value, force=False):
        """
        Set the value of a node.

        *Args:*\n
        _path_ - node path.\n
        _value_ - new value.\n
        _force_ - if TRUE path will be created. Default value is FALSE.\n

        *Raises:*\n
        _NoNodeError - node doesn't exist.\n
        _ZookeeperError - value is too large or server returns non-zero error code.
        """
        string_value = value.encode('utf-8')
        if (force):
            self.zk.ensure_path(path)
        self.zk.set(path, string_value)

    def get_value(self, path):
        """
        Get the value of a node.

        *Args:*\n
        _path_ - node path.

        *Returns:*\n
        Value of a node.

        *Raises:*\n
        _NoNodeError_ - node doesn't exist.\n
        _ZookeeperError_ - server returns a non-zero error code.
        """
        value, _stat = self.zk.get(path)
        return value

    def get_children(self, path):
        """
        Get a list of node's children.

        *Args:*\n
        _path_ - node path.

        *Returns:*\n
        List of node's children.

        *Raises:*\n
        _NoNodeError_ - node doesn't exist.\n
        _ZookeeperError_ - server returns a non-zero error code.
        """
        children = self.zk.get_children(path)
        return children