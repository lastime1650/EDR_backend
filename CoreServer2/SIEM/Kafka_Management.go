package siem

import (
	kafka_ "CoreServer/SIEM/kafka"
	"CoreServer/util"
	"sync"
)

//
//
//

// /
type KafkaManager struct {
	Kafka_Object *kafka_.Kafka
	Topic        string
	send_mutex_  *sync.Mutex
}

func New_KafkaManager(
	Topic string,
	ServerIP string,
	Port int,
	DefaultPartitions int,
	DefaultReplicationFactor int,
) *KafkaManager {

	if kafka_object, err := kafka_.NewKafka(
		kafka_.KafkaConfig{
			ServerIP:                 ServerIP,
			Port:                     Port,
			DefaultPartitions:        DefaultPartitions,
			DefaultReplicationFactor: DefaultReplicationFactor,
		},
	); err == nil {
		// 성공
		return &KafkaManager{
			Topic:        Topic,
			Kafka_Object: kafka_object,
			send_mutex_:  &sync.Mutex{},
		}
	} else {
		// 실패
		return nil
	}
}

func (kfM *KafkaManager) Send_to_Kafka(
	SendData map[string]interface{},
) error {
	kfM.send_mutex_.Lock()
	defer kfM.send_mutex_.Unlock()
	return kfM.Kafka_Object.SendMessage(
		kfM.Topic, //"siem-edr-processbhavior-event",
		util.ERROR_PROCESSING(util.Map_to_JSON(SendData)),
	)
}
