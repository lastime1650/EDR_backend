package util

import (
	"fmt"
	"net/url"
)

type IP_info struct {
	Query       string
	Status      string
	Country     string
	CountryCode string
	Region      string
	RegionName  string
	City        string
	Zip         string
	Lat         float64
	Lon         float64
	Timezone    string
	Isp         string
	Org         string
	As          string
	QueryString string
}

// IP -> JSON
func Get_IP_info(ip string) (*IP_info, error) {
	output, err := RestAPI_GET(
		"http://ip-api.com/json/"+ip,
		&url.Values{},
	)

	if err != nil {
		return nil, err
	}

	ip_maps, _ := JSON_to_Map(output)

	if ip_maps["status"] == "fail" {
		return nil, fmt.Errorf("Failed")
	} else {
		return &IP_info{
			Query:       ip_maps["query"].(string),
			Country:     ip_maps["country"].(string),
			CountryCode: ip_maps["countryCode"].(string),
			Region:      ip_maps["region"].(string),
			RegionName:  ip_maps["regionName"].(string),
			City:        ip_maps["city"].(string),
			Zip:         ip_maps["zip"].(string),
			Lat:         ip_maps["lat"].(float64),
			Lon:         ip_maps["lon"].(float64),
			Timezone:    ip_maps["timezone"].(string),
			Isp:         ip_maps["isp"].(string),
			Org:         ip_maps["org"].(string),
			As:          ip_maps["as"].(string),
		}, nil
	}

}
