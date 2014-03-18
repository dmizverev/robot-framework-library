# -*- coding: utf-8 -*-

import json
import jsonschema
import jsonpath

class JsonValidator(object):
    """
    Библиотека для проверки json.
    == Зависимости ==
    | jsonschema | https://pypi.python.org/pypi/jsonschema |
    | jsonpath | https://pypi.python.org/pypi/jsonpath |
    == Дополнительная информация == 
    - [ http://json-schema.org/ | Json Schema ]
    - [ http://www.jsonschema.net/ | Jsonschema generator ]
    - [ http://goessner.net/articles/JsonPath/ | JSONPath by Stefan Goessner ]
    - [ http://jsonpath.curiousconcept.com/ | JSONPath Tester ]
    == Пример использования ==
    Пример json, записанного в файле json_example.json
    | { "store": {
    |        "book": [ 
    |          { "category": "reference",
    |            "author": "Nigel Rees",
    |            "title": "Sayings of the Century",
    |            "price": 8.95
    |          },
    |          { "category": "fiction",
    |            "author": "Evelyn Waugh",
    |            "title": "Sword of Honour",
    |            "price": 12.99
    |          },
    |          { "category": "fiction",
    |            "author": "Herman Melville",
    |            "title": "Moby Dick",
    |            "isbn": "0-553-21311-3",
    |            "price": 8.99
    |          },
    |          { "category": "fiction",
    |            "author": "J. R. R. Tolkien",
    |            "title": "The Lord of the Rings",
    |            "isbn": "0-395-19395-8",
    |            "price": 22.99
    |          }
    |        ],
    |        "bicycle": {
    |          "color": "red",
    |          "price": 19.95
    |        }
    |  }
    | }
    
    | *Settings* | *Value* |
    | Library    | JsonValidator |
    | Library    | OperatingSystem |
    | *Test Cases* | *Action* | *Argument* | *Argument* |
    | Check element | ${json_example}=   | OperatingSystem.Get File |   ${CURDIR}${/}json_example.json |
    | | Element should exist  |  ${json_example}  |  $..book[?(@.author=='Herman Melville')] |
    """

    ROBOT_LIBRARY_SCOPE = 'GLOBAL'

    def _validate_json(self, checked_json, schema):
        try:
            jsonschema.validate(checked_json, schema)
        except jsonschema.ValidationError , e:
            raise AssertionError ('Json validation error: ' + e.message)
        except jsonschema.SchemaError , e:
            raise AssertionError ('Json-schema error:' + e.message)

    def validate_jsonschema_from_file (self, input_json, path_to_schema):
        """
        Проверка json по схеме, загруженной из файла.
        
        *Args:*\n
        _input_json_ - json-строка; в дальнейшем сериализуется при помощи json.loads;\n
        _path_to_schema_ - путь к файлу со схемой json;
        
        *Raises:*\n
        ValueError in json.loads
        
        *Example:*\n
        | *Settings* | *Value* |
        | Library    | JsonValidator |
        | *Test Cases* | *Action* | *Argument* | *Argument* |
        | Simple | Validate jsonschema from file  |  {"foo":bar}  |  ${CURDIR}${/}schema.json |
        """

        schema = open(path_to_schema).read()
        load_input_json = self._parse_json (input_json)

        try:
            load_schema = json.loads(schema)
        except ValueError, e:
            raise AssertionError ('Error in schema: ' + e.message)

        self._validate_json (load_input_json, load_schema)

    def validate_jsonschema (self, input_json, input_schema):
        """
        Проверка json по схеме.
        
        *Args:*\n
        _input_json_ - json-строка; в дальнейшем сериализуется при помощи json.loads;\n
        _input_schema_ - схема в виде строки; в дальнейшем сериализуется при помощи json.loads.
        
        *Raises:*\n
        ValueError in json.loads
        
        *Example:*\n
        | *Settings* | *Value* |
        | Library    | JsonValidator |
        | Library    | OperatingSystem |
        | *Test Cases* | *Action* | *Argument* | *Argument* |
        | Simple | ${schema}=   | OperatingSystem.Get File |   ${CURDIR}${/}schema_valid.json |
        |  | Validate jsonschema  |  {"foo":bar}  |  ${schema} |
        """
        load_input_json = self._parse_json (input_json)

        try:
            load_schema = json.loads(input_schema)
        except ValueError, e:
            raise AssertionError ('Error in schema: ' + e.message)

        self._validate_json (load_input_json, load_schema)

    def _parse_json (self, source):
        try:
            load_input_json = json.loads(source)
        except ValueError, e:
            raise ValueError("Could not parse '%s' as JSON: %s" % (source, e))
        return    load_input_json

    def get_elements (self, input_json, expr, result_type = 'VALUE', debug = 0, use_eval = True):
        """
        Возвращает список элементов из _input_json_, соответствующих jsonpath выражению.
        
        *Args:*\n
        _input_json_ - json-строка; в дальнейшем сериализуется при помощи json.loads;\n
        _expr_ - jsonpath выражение;\n
        _result_type_ - тип возвращаемого значения; принимает значения VALUE - возвращается список из json-строк, 
                        IPATH - возвращается список значений, значение по умолчанию: VALUE\n
        _debug_ - выводить отладочную информацию, принимает значения 0 или 1;\n
        _use_eval_ - вычисление значений в _expr_, значение по умолчанию True.
        
        *Raises:*\n
        "Could not get elements by jsonpath expression" в случае отсутствия искомых элементов
        
        *Example:*\n
        | *Settings* | *Value* |
        | Library    | JsonValidator |
        | Library    | OperatingSystem |
        | *Test Cases* | *Action* | *Argument* | *Argument* |
        | Get json elements | ${json_example}=   | OperatingSystem.Get File |   ${CURDIR}${/}json_example.json |
        | |  ${json_elements} | Get elements  |  ${json_example}  |  $.store.book[*].author |
        | Get json elements with eval | ${json_example}=   | OperatingSystem.Get File |   ${CURDIR}${/}json_example.json | use_eval=${True} |
        | |  ${json_elements} | Get elements  |  ${json_example}  |  $..book[?(@.price<10)] |
        | |  Log  |  ${json_elements[0]} |
        =>\n
        [u'Nigel Rees', u'Evelyn Waugh', u'Herman Melville', u'J. R. R. Tolkien']\n
        {u'category': u'reference', u'price': 8.95, u'title': u'Sayings of the Century', u'author': u'Nigel Rees'}
        """

        load_input_json = self._parse_json (input_json)
        value = jsonpath.jsonpath (load_input_json, expr, result_type, int(debug), use_eval)

        if not value:
            raise AssertionError ('Could not get elements by jsonpath expression %s' % expr)
        return    value

    def element_should_exist (self, input_json, expr, debug = 0, use_eval = True):
        """
        Проверка существования одного или более элементов, соответствующих jsonpath выражению.
        
        *Args:*\n
        _input_json_ - json-строка; в дальнейшем сериализуется при помощи json.loads;\n
        _expr_ - jsonpath выражение;\n
        _debug_ - выводить отладочную информацию, принимает значения 0 или 1;\n
        _use_eval_ - вычисление значений в _expr_.
        
        *Raises:*\n
        "Elements does not exist" в случае отсутствия искомых элементов
        
        *Example:*\n
        | *Settings* | *Value* |
        | Library    | JsonValidator |
        | Library    | OperatingSystem |
        | *Test Cases* | *Action* | *Argument* | *Argument* |
        | Check element | ${json_example}=   | OperatingSystem.Get File |   ${CURDIR}${/}json_example.json |
        | | Element should exist  |  ${json_example}  |  $..book[?(@.author=='Herman Melville')] |
        """

        try:
            self.get_elements (input_json, expr, debug = debug, use_eval = use_eval)
        except Exception:
            raise AssertionError ('Elements %s does not exist' % expr)

    def element_should_not_exist (self, input_json, expr, debug = 0, use_eval = True):
        """
        Проверка отсутствия одного или более элементов, соответствующих jsonpath выражению.
        
        Описание параметров и примеры смотри в кейворде [ #Element should exist | Element should exist ]
        """

        try:
            self.get_elements (input_json, expr, debug = debug, use_eval = use_eval)
        except Exception:
            return
        raise AssertionError ('Elements %s exist but should not' % expr)
