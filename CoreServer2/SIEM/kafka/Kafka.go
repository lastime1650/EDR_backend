package siem

import (
	"context"
	"errors"
	"fmt"
	"log"
	"net"
	"strconv"
	"sync"
	"time"

	kafka "github.com/segmentio/kafka-go"
	// Use explicit topics package if needed for older versions, but CreateTopics is on Conn now.
)

type Kafka struct {
	kafkaWriter *kafka.Writer
	adminConn   *kafka.Conn // Connection for administrative tasks
	brokers     []string
	topicCache  map[string]bool // Cache to avoid repeated checks/creation attempts
	cacheMutex  sync.RWMutex    // Mutex to protect the cache
	// Default configuration for auto-created topics
	defaultPartitions        int
	defaultReplicationFactor int

	check_init bool
}

// Configuration options for NewKafka
type KafkaConfig struct {
	ServerIP                 string
	Port                     int
	DefaultPartitions        int // Defaults to 1 if <= 0
	DefaultReplicationFactor int // Defaults to 1 if <= 0
}

func NewKafka(config KafkaConfig) (*Kafka, error) {
	brokers := []string{fmt.Sprintf("%s:%d", config.ServerIP, config.Port)}

	// Create a writer
	w := &kafka.Writer{
		Addr:         kafka.TCP(brokers...),
		Balancer:     &kafka.LeastBytes{},
		RequiredAcks: kafka.RequireOne, // Or kafka.RequireAll for more durability
		Async:        true,             // Set to true for higher throughput, but handle errors differently
		BatchSize:    30,               // 버퍼 크기 (너무 실시간이면 터짐)
		BatchTimeout: 10 * time.Second,
	}

	// 카프카 서버 검증 체크
	if _, err := check_Kafka_Server(brokers[0]); err != nil {
		return nil, err
	}

	// 카프카 서버 찾았을 때
	controllerAddr := brokers[0]

	adminConn, err := kafka.Dial("tcp", controllerAddr)
	if err != nil {
		w.Close()
		return nil, fmt.Errorf("failed to dial Kafka controller %s for admin tasks: %w", controllerAddr, err)
	}

	// 해당 카프카 기본 파티션값
	// 파티션 수 DefaultPartitions
	// 복제 수 DefaultReplicationFactor
	partitions := config.DefaultPartitions
	if partitions <= 0 {
		partitions = 1 // Sensible default
	}
	replicationFactor := config.DefaultReplicationFactor
	if replicationFactor <= 0 {
		replicationFactor = 1 // Sensible default (only works for single-node clusters)
		// For multi-node clusters, this should ideally be >= number of brokers you want for fault tolerance (e.g., 3)
		// You might need logic to determine cluster size or make this configurable based on environment.
		log.Printf("Warning: DefaultReplicationFactor set to 1. This is only suitable for single-node clusters or development.")
	}

	return &Kafka{
		kafkaWriter: w,
		adminConn:   adminConn, // 메인 컨트롤
		brokers:     brokers,   // 브로커

		topicCache: make(map[string]bool),
		cacheMutex: sync.RWMutex{},

		defaultPartitions:        partitions,
		defaultReplicationFactor: replicationFactor,

		check_init: true,
	}, nil
}

// ensureTopicExists checks if a topic exists and creates it if it doesn't.
// It uses a local cache to avoid repeated checks.
func (k *Kafka) ensureTopicExists(topic string) error {
	// 1. Check cache (read lock)
	k.cacheMutex.RLock()
	exists, found := k.topicCache[topic]
	k.cacheMutex.RUnlock()

	if found && exists {
		return nil // Topic is known to exist
	}

	// 2. Topic not in cache or known not to exist, need potential creation (write lock)
	k.cacheMutex.Lock()
	defer k.cacheMutex.Unlock()

	// 3. Double-check cache after acquiring write lock (another goroutine might have created it)
	exists, found = k.topicCache[topic]
	if found && exists {
		return nil
	}

	// 4. Check with Kafka broker if topic exists
	log.Printf("Topic '%s' not in cache, checking with Kafka broker...", topic)
	metadata, err := k.adminConn.ReadPartitions(topic) // Attempt to read partitions as existence check
	if err == nil && len(metadata) > 0 {
		log.Printf("Topic '%s' found on broker.", topic)
		k.topicCache[topic] = true // Update cache
		return nil
	}
	/*
		// Handle specific error types if ReadPartitions provides them
		// Example: Check if error indicates "Unknown Topic or Partition"
		if err != nil && !errors.Is(err, kafka.UnknownTopicOrPartition) && !isNetworkOrTimeoutError(err) {
			// Don't try to create if it's a more serious error (e.g., auth)
			log.Printf("Error checking topic '%s' existence (will not attempt creation): %v", topic, err)
			// Optionally cache this as false? Depends on whether the error is permanent.
			// k.topicCache[topic] = false
			return fmt.Errorf("failed to check topic '%s' existence: %w", topic, err)
		}
	*/
	// 5. Topic does not exist, attempt to create it
	log.Printf("Topic '%s' does not exist. Attempting to create...", topic)
	topicConfig := kafka.TopicConfig{
		Topic:             topic,
		NumPartitions:     k.defaultPartitions,
		ReplicationFactor: k.defaultReplicationFactor,
	}

	// Use the admin connection associated with the Kafka struct
	createErr := k.adminConn.CreateTopics(topicConfig)

	if createErr != nil {

		// If creation truly failed for another reason
		log.Printf("Failed to create topic '%s': %v", topic, createErr)
		k.topicCache[topic] = false // Mark as failed (might retry later if appropriate)
		return fmt.Errorf("failed to create topic '%s': %w", topic, createErr)
	}

	log.Printf("Successfully created topic '%s' with %d partitions and replication factor %d.", topic, k.defaultPartitions, k.defaultReplicationFactor)
	k.topicCache[topic] = true // Update cache

	// Optional: Wait a short moment for the topic creation to propagate through the cluster,
	// although usually writing immediately after a successful CreateTopics response is fine.
	// time.Sleep(500 * time.Millisecond)

	return nil
}

// SendMessage sends a message to the specified topic.
// If the topic doesn't exist, it attempts to create it first.
func (k *Kafka) SendMessage(topic string, message string) error {
	// Ensure the topic exists before trying to send
	if k.check_init {
		err := k.ensureTopicExists(topic)
		if err != nil {
			// If we couldn't ensure topic existence (check failed or creation failed), return error
			return fmt.Errorf("failed to ensure topic '%s' exists before sending: %w", topic, err)
		}
		k.check_init = false
	}

	// Topic should exist now (either pre-existing or just created)
	msg := kafka.Message{
		Topic: topic,
		Value: []byte(message),
		// Key: []byte("optional-key"), // Add a key if partitioning is important
	}
	//fmt.Printf("카프카 전달 -> %s \n", message)

	// Use a context with a timeout for the write operation
	ctx, cancel := context.WithTimeout(context.Background(), 8*time.Second) // 10-second timeout
	defer cancel()
	//fmt.Printf("카프카 전달 시작\n")
	err := k.kafkaWriter.WriteMessages(ctx, msg)
	if err != nil {
		fmt.Printf("카프카 전달 실패 %v \n", err)
		// Handle specific write errors if necessary
		if errors.Is(err, context.DeadlineExceeded) {
			log.Printf("Timeout writing message to topic %s: %v", topic, err)
			// Consider retries or other strategies
		} else if errors.Is(err, kafka.LeaderNotAvailable) || errors.Is(err, kafka.NotLeaderForPartition) {
			log.Printf("Leader not available for topic %s, might resolve automatically: %v", topic, err)
			// Writer might handle retries internally, but good to log
		} else {
			log.Printf("Failed to write message to topic %s: %v", topic, err)
		}

		// Attempt to clear the possibly stale topic cache entry if write fails, forcing re-check next time
		// Use write lock for cache modification
		k.cacheMutex.Lock()
		delete(k.topicCache, topic)
		k.cacheMutex.Unlock()
		log.Printf("Cleared cache for topic '%s' due to write error.", topic)

		return fmt.Errorf("failed to write message to topic '%s': %w", topic, err)
	}
	//fmt.Printf("카프카 전달 성공 %v \n", err)
	// log.Printf("Successfully sent message to topic %s", topic) // Optional: Log success
	return nil
}

// Close closes the Kafka writer and the admin connection.
func (k *Kafka) Close() error {
	log.Println("Closing Kafka resources...")
	var writerErr, adminErr error

	if k.kafkaWriter != nil {
		writerErr = k.kafkaWriter.Close()
		if writerErr != nil {
			log.Printf("Error closing Kafka writer: %v", writerErr)
		}
	}
	if k.adminConn != nil {
		adminErr = k.adminConn.Close()
		if adminErr != nil {
			log.Printf("Error closing Kafka admin connection: %v", adminErr)
		}
	}

	if writerErr != nil || adminErr != nil {
		return fmt.Errorf("errors occurred during Kafka close: writer_err=%v, admin_err=%v", writerErr, adminErr)
	}
	log.Println("Kafka resources closed.")
	return nil
}

// Helper function to check for common network/timeout errors during topic check
// (You might need to expand this based on observed errors)
func isNetworkOrTimeoutError(err error) bool {
	if errors.Is(err, context.DeadlineExceeded) {
		return true
	}
	var netErr net.Error
	if errors.As(err, &netErr) && netErr.Timeout() {
		return true
	}
	// Add other specific network-related errors if needed
	// e.g., syscall.ECONNREFUSED, etc. might require importing "syscall"
	return false
}

///
///
///

func check_Kafka_Server(broker string) (bool, error) {
	// Create a connection for administrative tasks (like creating topics)
	// We connect to the first broker, assuming it can handle admin requests or redirect.
	conn, err := kafka.Dial("tcp", broker)
	if err != nil {
		//w.Close() // Clean up writer if admin connection fails
		return false, fmt.Errorf("failed to dial Kafka for admin connection: %w", err)
	}

	// Check controller (optional but good practice)
	controller, err := conn.Controller()
	if err != nil {
		conn.Close()
		//w.Close()
		return false, fmt.Errorf("failed to get Kafka controller: %w", err)
	}
	controllerAddr := net.JoinHostPort(controller.Host, strconv.Itoa(controller.Port))
	log.Printf("Kafka Controller found at: %s\n", controllerAddr)

	// Close the initial connection and connect to the controller for admin tasks
	conn.Close()
	return true, nil
}
