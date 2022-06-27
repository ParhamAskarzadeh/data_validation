import sys

from jsonschema import validate
from kafka import KafkaConsumer, KafkaProducer, KafkaAdminClient
from kafka.admin import NewTopic
from pymongo import MongoClient
import config
import json


class MongoDB:
    def __init__(self):
        client = MongoClient(config.MONGO_HOST, config.MONGO_PORT)
        self.db = client['mohaymen']
        self.collection = self.db['valid_data']


class Kafka:
    def __init__(self):
        try:
            admin = KafkaAdminClient(bootstrap_servers='localhost:9092')

            topic1 = NewTopic(name='validation-error',
                              num_partitions=1,
                              replication_factor=1)

            if topic1.name not in admin.list_topics():
                admin.create_topics(topic1)

        except Exception as e:
            print(type(e), e)

        self.producer = KafkaProducer(bootstrap_servers='localhost:9092',
                                      value_serializer=lambda x: json.dumps(x).encode('utf-8'))
        self.consumer = KafkaConsumer(bootstrap_servers="localhost:9092",
                                      auto_offset_reset='earliest',
                                      value_deserializer=lambda m: json.loads(m.decode('utf-8')))

        self.producer.send("raw_data",
                           {"id": 2387, "lead": "hello", "content": "how are you", "datetime": "2022-05-03T19:21:15Z"})


class Manager:
    def __init__(self, schema_path):
        self._db = MongoDB()
        self.kafka = Kafka()
        self._load_schema()
        self.schema_path = schema_path

    def _load_schema(self):
        with open(self.schema_path, 'r') as file:
            schema = json.loads(file.read())
        self.schema = schema
        return schema

    def __check_validation(self, json_doc):
        try:
            validate(instance=json_doc, schema=self.schema)
        except Exception as e:
            return {
                'json_doc': json_doc,
                'error_status': {
                    'is_error': True,
                    'message': e.message
                }
            }
        return {
            'json_doc': json_doc,
            'error_status': {
                'is_error': False,
                'message': None
            }
        }

    def run(self):
        self.kafka.consumer.subscribe(['raw_data'])

        for item in self.kafka.consumer:
            result = self.__check_validation(item)

            if result['error_status']['is_error'] is False:
                self._db.collection.insert_one(result['json_doc'])
            else:
                self.kafka.producer.send(topic="validation-error",
                                         value={"error": result['error_status']['message'], "data": result['json_doc']})


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("not enough parameters")
        exit(1)
    schema_path = sys.argv[2]
    manager = Manager(schema_path).run()

