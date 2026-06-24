/*
 * Copyright (c) 2026 PCL-CCNN
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package auth

import (
	"context"
	"fmt"
	"time"

	"github.com/ccnn-pcl/ccnn/app_examples/intelligent_doctor/medical_materials_service/config"
	"github.com/ccnn-pcl/ccnn/app_examples/intelligent_doctor/medical_materials_service/logger"
	"github.com/go-resty/resty/v2"
)

type verifyRequest struct {
	Token string `json:"token"`
}

type verifyResponse struct {
	Valid   bool   `json:"valid"`
	Message string `json:"message"`
}

func verifySignature(ctx context.Context, token string) error {
	verifyConfig := config.GetVerfierConfig()
	if verifyConfig.Url == "" {
		return fmt.Errorf("on verify url error")
	}
	client := resty.New().
		SetBaseURL(verifyConfig.Url).
		SetTimeout(time.Duration(verifyConfig.Timeout) * time.Second).
		SetRetryCount(3).
		SetRetryMaxWaitTime(3 * time.Second)

	client.OnAfterResponse(func(c *resty.Client, resp *resty.Response) error {
		logger.Log.Printf(
			"time: %v | status code: %d | URL: %s",
			resp.Time(), resp.StatusCode(), resp.Request.URL,
		)
		return nil
	})
	req := verifyRequest{
		Token: token,
	}
	var verResponse verifyResponse

	rsp, err := client.R().
		SetBody(req).
		SetContext(ctx).
		SetResult(&verResponse).
		Post(verifyConfig.Path)
	if err != nil {
		return err
	}
	if rsp.IsError() {
		logger.Log.Errorf("status %d msg %s", rsp.StatusCode(), rsp.Body())

		return fmt.Errorf("verify request error %s", rsp.Body())
	}
	if verResponse.Valid {
		logger.Log.Infof("send verify token request success %s", verResponse.Message)
		return nil
	}
	return fmt.Errorf("invalid error %s", verResponse.Message)
}
