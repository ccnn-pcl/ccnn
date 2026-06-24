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

	handler "github.com/ccnn-pcl/ccnn/app_examples/intelligent_doctor/medical_materials_service/api"
	apiModel "github.com/ccnn-pcl/ccnn/app_examples/intelligent_doctor/medical_materials_service/api/model"
	"github.com/ccnn-pcl/ccnn/app_examples/intelligent_doctor/medical_materials_service/logger"
	"github.com/google/jsonschema-go/jsonschema"
	"github.com/modelcontextprotocol/go-sdk/mcp"
)

func init() {
	in, err := jsonschema.For[apiModel.QueryVisitsInfoRequest](&jsonschema.ForOptions{})
	if err != nil {
		logger.Log.Fatal(err)
	}
	out, err := jsonschema.For[apiModel.QueryVisitsInfoResponse](&jsonschema.ForOptions{})
	if err != nil {
		logger.Log.Fatal(err)
	}
	registerTool(MCPTool[*apiModel.QueryVisitsInfoRequest, *apiModel.QueryVisitsInfoResponse]{
		Name:        "visits",
		Description: "获取患者历史就诊信息，可以根据症状关键字和时间进行检索",
		In:          in,
		Out:         out,
		Handler: func(ctx context.Context, request *mcp.CallToolRequest, in *apiModel.QueryVisitsInfoRequest) (*mcp.CallToolResult, *apiModel.QueryVisitsInfoResponse, error) {
			logger.Log.Infof("get one mcp tool call for user %v", in)

			result, err := runVisitTool(ctx, in)
			if err != nil {
				logger.Log.Errorf("run visit tool for user %s error %v", in.UserID, err)
				return nil, nil, err
			}
			logger.Log.Infof("query visits info for user %s success", in.UserID)
			return nil, result, nil
		},
	})
}

// your logic goes here
func runVisitTool(ctx context.Context, args *apiModel.QueryVisitsInfoRequest) (*apiModel.QueryVisitsInfoResponse, error) {
	// Implement your logic here
	return handler.QueryVisitsInfoHandler(ctx, args)
}
