package util

import (
	"bytes"
	"io"
	"net/http"
	"net/url"
)

/*
	그 어떤 서버든 간에,
	동일하게 RestAPI 쿼리가 가능해야한다.
*/

func RestAPI_GET(url string, params *url.Values) (string, error) {

	response, err := http.Get(url + "?" + params.Encode())
	if err != nil {
		return "", err
	}
	defer response.Body.Close()

	body, err := io.ReadAll(response.Body)
	if err != nil {
		return "", err
	}
	//fmt.Println(string(body))
	return string(body), nil
}

func RestAPI_POST(url string, data *[]byte) (string, error) {

	data_buf := bytes.NewBuffer(*data)

	if res, err := http.Post(url, "application/octet-stream", data_buf); err == nil && res != nil {
		// fmt.Println(res.Request.Response)
		defer res.Body.Close()

		body, err := io.ReadAll(res.Body)
		if err != nil {
			return "", err
		}
		return string(body), nil
	} else {
		return "", err
	}

	/*
		response, err := http.PostForm(url, *params)
		if err != nil {
			return "", err
		}
		defer response.Body.Close()

		body, err := io.ReadAll(response.Body)
		if err != nil {
			return "", err
		}
	*/

}
