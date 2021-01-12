from kafka import KafkaProducer
from kafka.errors import KafkaError
import json
from configs.kafka_setting import KAFKA_SETTING

producer = KafkaProducer(bootstrap_servers=KAFKA_SETTING['bootstrap_servers'])

partitions = producer.partitions_for(KAFKA_SETTING['topic'])
print('Topic下分区: %s' % partitions)
user_data = {
    "msg": "1",
    "search_dict":{
        'source_type': "江苏建设工程招标网"
    }
}

send_data = bytes(json.dumps(user_data), encoding="utf-8")

import time
try:
    index = 0
    while True:
        send_data = bytes(json.dumps(user_data), encoding="utf-8")
        future = producer.send(KAFKA_SETTING['topic'], send_data)
        print('send message succeed.')
        time.sleep(1)
        index += 1
        break
except KafkaError as e:
    print('send message failed. [e] ='),
