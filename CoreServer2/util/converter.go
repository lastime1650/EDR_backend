package util

import (
	"bytes"
	"encoding/base64"
	"encoding/binary"
	"math"
)

func Int32_to_Bytes(data int32) ([]byte, error) {
	buf := new(bytes.Buffer)
	err := binary.Write(buf, binary.LittleEndian, data)
	return buf.Bytes(), err
}

func Bytes_to_Int32(data []byte) (int32, error) {
	buf := new(bytes.Buffer)
	buf.Write(data)

	data_int32 := int32(0)
	err := binary.Read(buf, binary.LittleEndian, &data_int32)
	return data_int32, err
}

func UInt32_to_Bytes(data uint32) ([]byte, error) {
	buf := new(bytes.Buffer)
	err := binary.Write(buf, binary.LittleEndian, data)
	return buf.Bytes(), err
}

func Bytes_to_UInt32(data []byte) (uint32, error) {
	buf := new(bytes.Buffer)
	buf.Write(data)

	data_uint32 := uint32(0)
	err := binary.Read(buf, binary.LittleEndian, &data_uint32)
	return data_uint32, err
}

func UInt64_to_Bytes(data uint64) ([]byte, error) {
	buf := new(bytes.Buffer)
	err := binary.Write(buf, binary.LittleEndian, data)
	return buf.Bytes(), err
}

func Bytes_to_UInt64(data []byte) (uint64, error) {
	buf := new(bytes.Buffer)
	buf.Write(data)

	data_uint64 := uint64(0)
	err := binary.Read(buf, binary.LittleEndian, &data_uint64)
	return data_uint64, err
}

func Int64_to_Bytes(data int64) ([]byte, error) {
	buf := new(bytes.Buffer)
	err := binary.Write(buf, binary.LittleEndian, data)
	return buf.Bytes(), err
}

func Bytes_to_Int64(data []byte) (int64, error) {
	buf := new(bytes.Buffer)
	buf.Write(data)

	data_int64 := int64(0)
	err := binary.Read(buf, binary.LittleEndian, &data_int64)
	return data_int64, err
}

func Float64_to_uint32(input float64) uint32 {
	return uint32(math.Trunc(input))
}

// []byte to base64
func Bytes_to_Base64(data []byte) string {
	return base64.StdEncoding.EncodeToString(data)
}

func Int_to_Bool(data int64) bool {
	if data == 0 {
		return false
	} else {
		return true
	}
}

func Bool_to_Int(data bool) int {
	if data == false {
		return 0
	} else {
		return 1
	}
}
