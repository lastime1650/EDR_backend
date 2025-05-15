# EDR_backend
This repository is a backend resources for EDR

<br>

EDR 온라인 문서 -> [https://cominam-documents.gitbook.io/ai-edr-system](https://cominam-documents.gitbook.io/ai-edr-system)
-------------------

# Docker 이미지 기반 배포
이 EDR 백엔드는 도커 이미지 소스로 배포하며 
그 누구나 즉각적인 체험할 수 있도록 환경을 제공합니다.
<br>

### EDR 도커 실행을 위한 준비물 리스트

- 1) [Dockerfile](https://github.com/lastime1650/EDR_backend/blob/main/docker-compose.yml) ( 개발한 EDR 이미지 생성용 )
- 2) [docker-compose.yaml](https://github.com/lastime1650/EDR_backend/blob/main/docker-compose.yml) ( 의존성 이미지 한방! )

### 의존성 요구 도커 이미지 리스트

1. Elasticsearch (docker.elastic.co/elasticsearch/elasticsearch:8.17.4)
2. Kibana (docker.elastic.co/kibana/kibana:8.17.4)
3. Logstash (docker.elastic.co/logstash/logstash:8.17.4)
4. Kafka (confluentinc/cp-kafka:latest)
5. Kafka-Ui (provectuslabs/kafka-ui:latest)
6. Zookeeper (confluentinc/cp-zookeeper:latest)
7. MariaDB (mariadb:10.7)

-------------------
<br>

## Core Server - >= Golang 1.23

```
  1차 개발 완료
```

소스코드 -> [https://github.com/lastime1650/EDR_backend/tree/main/CoreServer2](https://github.com/lastime1650/EDR_backend/tree/main/CoreServer2)

How to work -> [https://cominam-documents.gitbook.io/ai-edr-system/edr/core-server](https://cominam-documents.gitbook.io/ai-edr-system/edr/core-server)

<br>

## Analysis Server - >= Python 3.9
```
  1차 개발 완료!
```
file -> [https://github.com/lastime1650/EDR_backend/tree/main/Analysis_Server](https://github.com/lastime1650/EDR_backend/tree/main/Analysis_Server) <br>
here is description -> [https://cominam-documents.gitbook.io/cominam-edr/edr-backend/analysis-server](https://cominam-documents.gitbook.io/cominam-edr/edr-backend/analysis-server)
<br>

## Web Server - >= Python 3.9
```
  Preparing ...
```
<br>
