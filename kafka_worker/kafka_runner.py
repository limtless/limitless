#!/usr/bin/env python
import time
import traceback
import json
from kafka import KafkaAdminClient, KafkaConsumer
from kafka.admin import NewTopic
from concurrent import  futures
from configs.kafka_setting import KAFKA_SETTING
from configs.logging_settings import LogStateString

from spidertools.db_utils.mongdb_utils import get_mongo_connect
from utils.worker_utils import single_html_extact,parse_callback
from utils.logger_utils import savelog
from project_setting import MongoUrl



def work_node(message):
    savelog(LogStateString.Info_KafkaMessage,msg_dict=message.value)
    try:
        _, mongo_db = get_mongo_connect(mongo_url=MongoUrl)  # git  # "mongodb://localhost:27017") #
        search_condition = message.value['search_dict']
        search_condition['is_parsed'] = 0
        mongo_table = mongo_db['project_html']
        total_count = mongo_table.find(search_condition).count()

        for i in range(int(total_count / 100) + 1):
            items = mongo_table.find(search_condition).limit(100)
            for item in items:
                output = single_html_extact(item)
                parse_callback(output,mongo_db)
    except Exception as e:
        savelog(LogStateString.FatalError, traceback.format_exc(), msg_dict=message.value)


def main():
    try:
        admin = KafkaAdminClient(bootstrap_servers=KAFKA_SETTING['bootstrap_servers'])
        topic = NewTopic(**KAFKA_SETTING['topic_params'])
        admin.create_topics([topic])
    except Exception:
        pass


    consumer = KafkaConsumer(bootstrap_servers=KAFKA_SETTING['bootstrap_servers'],
                             auto_offset_reset=KAFKA_SETTING['auto_offset_reset'],
                             consumer_timeout_ms=KAFKA_SETTING['consumer_timeout_ms'],
                             value_deserializer=lambda m: json.loads(m.decode('utf-8')))
    consumer.subscribe(KAFKA_SETTING['topic'])


    working_pool = futures.ProcessPoolExecutor(4)
    while True:
        start_time = time.time()
        working_pool.map(work_node,consumer)
        print("checking")
        print("time_cost:"+str(time.time() - start_time))



if __name__ == "__main__":
    main()