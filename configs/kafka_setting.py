from project_setting import DEBUG


KAFKA_SETTING = {
        "auto_offset_reset":"latest",
        "consumer_timeout_ms":1000,
        'topic': 'crmproject',
        'groupid':'crmproject',
        "num_partitions":1,
        "topic_params":{
            "name":'crmproject',
            "num_partitions":1,
            "replication_factor":1,
        }
    }



if DEBUG:
    KAFKA_SETTING['bootstrap_servers'] = ["localhost:9092"]
else:
    KAFKA_SETTING['bootstrap_servers'] = ["192.168.2.130:6667",'192.168.2.131:6667',"192.168.2.132:6667","192.168.2.133:6667","192.168.2.134:6667"]

