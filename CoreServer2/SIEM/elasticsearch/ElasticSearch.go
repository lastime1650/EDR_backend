package siem

import (
	"bytes"
	"fmt"

	"github.com/elastic/go-elasticsearch/v8"
)

// ELK 관련 함수정의

// 템플릿 생성 (이미 있는 경우는 제외)

type ElasticSearch struct {
	es *elasticsearch.Client
}

func New_ElasticSearch(config elasticsearch.Config) *ElasticSearch {

	// 엘라스틱서치 클라이언트 오브젝트 생성
	es, err := elasticsearch.NewClient(config)
	if err != nil {
		fmt.Println(err)
		panic(err)
	}

	// 연결확인
	res, err := es.Info()
	if err != nil {
		fmt.Println(err)
		panic(err)
	}
	fmt.Printf("연결 응답 %v \n", res)

	return &ElasticSearch{
		es: es,
	}
}

// 인덱스 생성
func (as *ElasticSearch) Create_index(index string) (bool, error) {
	// 1. 존재여부 확인
	exists, err := as.is_exists_index(index)
	if err != nil {
		return false, err
	}

	if exists {
		fmt.Printf("이미 %v 인덱스는 존재함.\n", index)
		return false, nil
	} else {
		// 2. 생성
		res, err := as.es.Indices.Create(index)
		if err != nil {
			return false, err
		}
		fmt.Printf("index 생성 응답 %v \n", res)
		return true, nil
	}
}

// 인덱스 탬플릿 생성/추가
func (as *ElasticSearch) Create_template(index_name string, json_template string) (bool, error) {

	// 이미 존재하는 지 체크
	is_exists, err := as.is_exists_template(index_name)
	if err != nil {
		return false, err
	}
	if is_exists {
		fmt.Printf("이미 %v 템플릿이 존재함.\n", index_name)
		return false, fmt.Errorf("이미 %v 템플릿이 존재함.", index_name)
	} else {
		a := bytes.NewReader([]byte(json_template))

		res, _ := as.es.Indices.PutIndexTemplate(index_name, a)
		fmt.Printf("template 생성 응답 %v \n", res)
		if res.StatusCode != 200 {
			return false, fmt.Errorf("template 생성 응답 %v \n", res)
		} else {
			return true, nil
		}

	}

}

// 컴포넌트 템플릿 생성
func (as *ElasticSearch) Create_component_template(template_name string, json_template string) (bool, error) {
	is_exists_component_template, err := as.es.Cluster.ExistsComponentTemplate(template_name)
	if err != nil {
		return false, err
	}
	if is_exists_component_template.StatusCode == 200 {
		fmt.Printf("이미 %v 컴포넌트 템플릿이 존재함.\n", template_name)
		return false, nil
	} else {
		a := bytes.NewReader([]byte(json_template))
		res, _ := as.es.Cluster.PutComponentTemplate(template_name, a)
		fmt.Printf("component template 생성 응답 %v \n", res)
		if res.StatusCode != 200 {
			return false, fmt.Errorf("component template 생성 응답 %v \n", res)
		} else {
			return true, nil
		}
	}
}

// Document 추가
func (as *ElasticSearch) AddDocument(index_name string, json_template string) (bool, error) {
	// 이미 존재하는 지 체크
	is_exists, err := as.is_exists_index(index_name)
	if err != nil {
		return false, err
	}
	if !is_exists {
		return false, fmt.Errorf("인덱스 %v 존재하지 않습니다.", index_name)
	}

	a := bytes.NewReader([]byte(json_template))

	res, err := as.es.Index(index_name, a)
	if err != nil {
		return false, err
	}
	fmt.Printf("document 추가 응답 %v \n", res)
	if res.StatusCode != 200 {
		return false, fmt.Errorf("document 추가 응답 %v \n", res)
	} else {
		return true, nil
	}
}

// 인덱스 존재여부 확인
func (as *ElasticSearch) is_exists_index(index string) (bool, error) {
	res, err := as.es.Indices.Exists([]string{index})
	if err != nil {
		return false, err
	}

	// http 응답 코드에 따라 여부 확인
	if res.StatusCode == 200 {
		return true, nil
	} else {
		return false, nil
	}
}

// 템플릿 존재여부 확인
func (as *ElasticSearch) is_exists_template(template_name string) (bool, error) {
	res, err := as.es.Indices.ExistsIndexTemplate(template_name) // V2 템플릿
	if err != nil || res.StatusCode != 200 {
		return false, nil
	} else {
		return true, nil
	}
}

/*
// IP-API.com 에서 제공하는 IP 정보 가져오기
func (as *ElasticSearch) Get_IP_info(ip string) (map[string]interface{}, error) {

	ip_result, err := util.Get_IP_info(ip)
	if err != nil {
		return nil, err
	}

	// 공용 index 템플릿 규격으로 변환
	output := map[string]interface{}{
		"Ip":         ip_result["query"],
		"Country":    ip_result["country"],
		"Region":     ip_result["region"],
		"RegionName": ip_result["regionName"],
		"TimeZone":   ip_result["timezone"],
		"City":       ip_result["city"],
		"Zip":        ip_result["zip"],
		"Isp":        ip_result["isp"],
		"Org":        ip_result["org"],
		"As":         ip_result["as"],
		"location": map[string]interface{}{
			"lat": ip_result["lat"],
			"lon": ip_result["lon"],
		},
	}

	return output, nil
}
*/
