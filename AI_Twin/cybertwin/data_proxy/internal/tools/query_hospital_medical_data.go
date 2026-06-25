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

package tools

import (
	"context"

	"github.com/ccnn-pcl/ccnn/AI_Twin/cybertwin/data_proxy/handler"
	"github.com/ccnn-pcl/ccnn/AI_Twin/cybertwin/data_proxy/logger"
	"github.com/google/jsonschema-go/jsonschema"
	"github.com/modelcontextprotocol/go-sdk/mcp"
)

func init() {
	in, err := jsonschema.For[handler.GetHospitalDataRequest](&jsonschema.ForOptions{})
	if err != nil {
		logger.Log.Fatal(err)
	}
	out, err := jsonschema.For[handler.HospitalDataResponse](&jsonschema.ForOptions{})
	if err != nil {
		logger.Log.Fatal(err)
	}
	registerTool(MCPTool[*handler.GetHospitalDataRequest, *handler.HospitalDataResponse]{
		Name:        "query_hospital_medical_data",
		Description: "获取查询医疗数据服务信息",
		In:          in,
		Out:         out,
		Handler: func(ctx context.Context, request *mcp.CallToolRequest, in *handler.GetHospitalDataRequest) (*mcp.CallToolResult, *handler.HospitalDataResponse, error) {
			logger.Log.Infof("get one mcp tool call for query %v", in)

			result, err := runQueryHospitialDataTool(ctx, in)
			if err != nil {
				logger.Log.Errorf("run query hospital medical data tool for user %s error %v", in.UserID, err)
				return nil, nil, err
			}
			logger.Log.Infof("query hospitial medical data info for user %s success", in.UserID)
			return nil, result, nil
		},
	})
}

// your logic goes here
func runQueryHospitialDataTool(ctx context.Context, args *handler.GetHospitalDataRequest) (*handler.HospitalDataResponse, error) {
	// Implement your logic here
	h := handler.NewDataHandler()

	return h.GetHospitalMedicalData(ctx, args)
}
