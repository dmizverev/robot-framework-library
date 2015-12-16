# -*- coding: utf-8 -*-

import json
import jsonschema
from jsonpath_rw import parse
from jsonselect import jsonselect

class JsonValidator(object):
    """
    Библиотека для проверки json.
    Основана на: JSONSchema, JSONPath, JSONSelect.

    == Дополнительная информация == 
    - [ http://json-schema.org/ | Json Schema ]
    - [ http://www.jsonschema.net/ | Jsonschema generator ]
    - [ http://goessner.net/articles/JsonPath/ | JSONPath by Stefan Goessner ]
    - [ http://jsonpath.curiousconcept.com/ | JSONPath Tester ]
    - [ http://jsonselect.org/ | JSONSelect]
    - [ http://jsonselect.curiousconcept.com/ | JSONSelect Tester]

    == Зависимости ==
    | jsonschema | https://pypi.python.org/pypi/jsonschema |
    | jsonpath-rw | https://pypi.python.org/pypi/jsonpath-rw |
    | jsonselect | https://pypi.python.org/pypi/jsonselect |

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
    | | Element should exist  |  ${json_example}  |  .author:contains("Evelyn Waugh") |
    """

    ROBOT_LIBRARY_SCOPE='GLOBAL'

    def _validate_json(self, checked_json, schema):
        """
        Проверка json по JSONSchema
        """
        
        try:
            jsonschema.validate(checked_json, schema)
        except jsonschema.ValidationError , e:
            raise JsonValidatorError ('Element: %s. Error: %s. '%(e.path[0], e.message))
        except jsonschema.SchemaError , e:
            raise JsonValidatorError ('Json-schema error:'+e.message)

    def validate_jsonschema_from_file (self, json_string, path_to_schema):
        """
        Проверка json по схеме, загружаемой из файла.
        
        *Args:*\n
        _json_string_ - json-строка;\n
        _path_to_schema_ - путь к файлу со схемой json;
        
        *Raises:*\n
        JsonValidatorError
        
        *Example:*\n
        | *Settings* | *Value* |
        | Library    | JsonValidator |
        | *Test Cases* | *Action* | *Argument* | *Argument* |
        | Simple | Validate jsonschema from file  |  {"foo":bar}  |  ${CURDIR}${/}schema.json |
        """

        schema=open(path_to_schema).read()
        load_input_json=self.string_to_json (json_string)

        try:
            load_schema=json.loads(schema)
        except ValueError, e:
            raise JsonValidatorError ('Error in schema: '+e.message)

        self._validate_json (load_input_json, load_schema)

    def validate_jsonschema (self, json_string, input_schema):
        """
        Проверка json по схеме.
        
        *Args:*\n
        _json_string_ - json-строка;\n
        _input_schema_ - схема в виде строки;
        
        *Raises:*\n
        JsonValidatorError
        
        *Example:*\n
        | *Settings* | *Value* |
        | Library    | JsonValidator |
        | Library    | OperatingSystem |
        | *Test Cases* | *Action* | *Argument* | *Argument* |
        | Simple | ${schema}=   | OperatingSystem.Get File |   ${CURDIR}${/}schema_valid.json |
        |  | Validate jsonschema  |  {"foo":bar}  |  ${schema} |
        """

        load_input_json=self.string_to_json (json_string)

        try:
            load_schema=json.loads(input_schema)
        except ValueError, e:
            raise JsonValidatorError ('Error in schema: '+e.message)

        self._validate_json (load_input_json, load_schema)

    def string_to_json (self, source):
        """
        Десериализация строки в json структуру.
        
        *Args:*\n
        _source_ - json-строка
        
        *Return:*\n
        Json структура
        
        *Raises:*\n
        JsonValidatorError
        
        *Example:*\n
        | *Settings* | *Value* |
        | Library    | JsonValidator |
        | Library    | OperatingSystem |
        | *Test Cases* | *Action* | *Argument* | *Argument* |
        | String to json  | ${json_string}=   | OperatingSystem.Get File |   ${CURDIR}${/}json_example.json |
        |                 |  ${json}= | String to json  |  ${json_string} |
        |                 |  Log | ${json["store"]["book"][0]["price"]} |
        =>\n
        8.95
        """
        
        try:
            load_input_json=json.loads(source)
        except ValueError, e:
            raise JsonValidatorError("Could not parse '%s' as JSON: %s"%(source, e))
        return    load_input_json

    def json_to_string (self, source):
        """
        Cериализация json структуры в строку.
        
        *Args:*\n
        _source_ - json структура
        
        *Return:*\n
        Json строка
        
        *Raises:*\n
        JsonValidatorError
        
        *Example:*\n
        | *Settings* | *Value* |
        | Library    | JsonValidator |
        | Library    | OperatingSystem |
        | *Test Cases* | *Action* | *Argument* | *Argument* |
        | Json to string  | ${json_string}=   | OperatingSystem.Get File |   ${CURDIR}${/}json_example.json |
        |                 | ${json}= | String to json |   ${json_string} |
        |                 | ${string}=  |  Json to string  |  ${json} |
        |                 | ${pretty_string}=  |  Pretty print json  |  ${string} |
        |                 | Log to console  |  ${pretty_string} |
        """
        
        try:
            load_input_json=json.dumps(source)
        except ValueError, e:
            raise JsonValidatorError("Could serialize '%s' to JSON: %s"%(source, e))
        return    load_input_json
    
    def get_elements (self, json_string, expr):
        """
        Возвращает список элементов из _json_string_, соответствующих [http://goessner.net/articles/JsonPath/|JSONPath] выражению.
        
        *Args:*\n
        _json_string_ - json-строка;\n
        _expr_ - JSONPath выражение;
        
        *Return:*\n
        Список найденных элементов. Если элементы не найдены, то возвращается ``None``
        
        *Example:*\n
        | *Settings* | *Value* |
        | Library    | JsonValidator |
        | Library    | OperatingSystem |
        | *Test Cases* | *Action* | *Argument* | *Argument* |
        | Get json elements | ${json_example}=   | OperatingSystem.Get File |   ${CURDIR}${/}json_example.json |
        |                   |  ${json_elements}= | Get elements  |  ${json_example}  |  $.store.book[*].author |
        =>\n
        | [u'Nigel Rees', u'Evelyn Waugh', u'Herman Melville', u'J. R. R. Tolkien']
        """

        load_input_json=self.string_to_json (json_string)
        # парсинг jsonpath
        jsonpath_expr=parse(expr)
        # список возвращаемых элементов
        value_list=[]
        for match in jsonpath_expr.find(load_input_json):
            value_list.append(match.value)
        if not value_list:
            return None
        else:
            return value_list

    def select_elements (self, json_string, expr):
        """
        Возвращает список элементов из _json_string_, соответствующих [ http://jsonselect.org/ | JSONSelect] выражению.
        
        *Args:*\n
        _json_string_ - json-строка;\n
        _expr_ - JSONSelect выражение;
        
        *Return:*\n
        Список найденных элементов. Если элементы не найдены, то ``None``
        
        *Example:*\n
        | *Settings* | *Value* |
        | Library    | JsonValidator |
        | Library    | OperatingSystem |
        | *Test Cases* | *Action* | *Argument* | *Argument* |
        | Select json elements | ${json_example}=   | OperatingSystem.Get File |   ${CURDIR}${/}json_example.json |
        |                      |  ${json_elements}= | Select elements  |  ${json_example}  |  .author:contains("Evelyn Waugh")~.price |
        =>\n
        | 12.99
        """

        load_input_json=self.string_to_json (json_string)
        # парсинг jsonselect
        jsonselect.Parser(load_input_json)
        values=jsonselect.select(expr, load_input_json)
        return values

    def element_should_exist (self, json_string, expr):
        """
        Проверка существования одного или более элементов, соответствующих [ http://jsonselect.org/ | JSONSelect] выражению.
        
        *Args:*\n
        _json_string_ - json-строка;\n
        _expr_ - jsonpath выражение;\n
        
        *Raises:*\n
        JsonValidatorError
        
        *Example:*\n
        | *Settings* | *Value* |
        | Library    | JsonValidator |
        | Library    | OperatingSystem |
        | *Test Cases* | *Action* | *Argument* | *Argument* |
        | Check element | ${json_example}=   | OperatingSystem.Get File |   ${CURDIR}${/}json_example.json |
        | | Element should exist  |  ${json_example}  |  $..book[?(@.author=='Herman Melville')] |
        """

        value=self.select_elements (json_string, expr)
        if value is None:
            raise JsonValidatorError ('Elements %s does not exist'%expr)

    def element_should_not_exist (self, json_string, expr):
        """
        Проверка отсутствия одного или более элементов, соответствующих [ http://jsonselect.org/ | JSONSelect] выражению.
        
        *Args:*\n
        _json_string_ - json-строка;\n
        _expr_ - jsonpath выражение;\n
        
        *Raises:*\n
        JsonValidatorError
        """

        value=self.select_elements (json_string, expr)
        if value is not None:
            raise JsonValidatorError ('Elements %s exist but should not'%expr)

    def update_json(self, json_string, expr, value, index=0):
        """
        Замена значения в json-строке.

        *Args:*\n
        _json_string_ - json-строка dict;\n
        _expr_ - JSONPath выражение для определения заменяемого значения;\n
        _value_ - значение, на которое будет произведена замена;\n
        _index_ - устанавливает индекс для выбора элемента внутри списка совпадений, по-умолчанию равен 0;\n
        
        *Return:*\n
        Изменённый json в виде словаря.

        *Example:*\n
        | *Settings* | *Value* |
        | Library    | JsonValidator |
        | Library    | OperatingSystem |
        | *Test Cases* | *Action* | *Argument* | *Argument* |
        | Update element | ${json_example}=   | OperatingSystem.Get File |   ${CURDIR}${/}json_example.json |
        | | ${json_update}= | Update_json  |  ${json_example}  |  $..color  |  changed |
        """

        load_input_json=self.string_to_json (json_string)
        matches = self._json_path_search(load_input_json, expr)

        datum_object = matches[int(index)]

        if not isinstance(datum_object, DatumInContext):
            raise JsonValidatorError("Nothing found by the given json-path")

        path = datum_object.path

        # Изменить справочник используя полученные данные
        # Если пользователь указал на список
        if isinstance(path, Index):
            datum_object.context.value[datum_object.path.index] = value
        # Если пользователь указал на значение (string, bool, integer or complex)
        elif isinstance(path, Fields):
            datum_object.context.value[datum_object.path.fields[0]] = value
            
        return load_input_json

    def pretty_print_json (self, json_string):
        """
        Возврещает отформатированную json-строку _json_string_.\n
        Используется метод json.dumps с настройкой _indent=2, ensure_ascii=False_.
        
        *Args:*\n
        _json_string_ - json-строка.
        
        *Example:*\n
        | *Settings* | *Value* |
        | Library    | JsonValidator |
        | Library    | OperatingSystem |
        | *Test Cases* | *Action* | *Argument* | *Argument* |
        | Check element | ${pretty_json}=   | Pretty print json |   {a:1,foo:[{b:2,c:3},{d:"baz",e:4}]} |
        | | Log  |  ${pretty_json}  |
        =>\n
        | {
        |    "a": 1, 
        |    "foo": [
        |      {
        |        "c": 3, 
        |        "b": 2
        |      }, 
        |      {
        |        "e": 4, 
        |        "d": "baz"
        |      }
        |    ]
        | }
        """

        return json.dumps(self.string_to_json(json_string), indent=2, ensure_ascii=False)

class JsonValidatorError(Exception):
    pass
