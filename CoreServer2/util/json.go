package util

import (
	"encoding/json"
)

func Map_to_JSON(data any) (string, error) {
	json_byte, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return "", err
	}
	return string(json_byte), nil
}
func Map_to_JSON2(data any) ([]byte, error) {
	json_byte, err := json.Marshal(data)
	if err != nil {
		return []byte{}, err
	}
	return json_byte, nil
}

func JSON_to_Map(JSON string) (map[string]interface{}, error) {
	data := make(map[string]interface{})
	if err := json.Unmarshal([]byte(JSON), &data); err != nil {
		return nil, err
	} else {
		return data, nil
	}
}
