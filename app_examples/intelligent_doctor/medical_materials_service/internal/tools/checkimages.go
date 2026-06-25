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
	"encoding/base64"

	handler "github.com/ccnn-pcl/ccnn/app_examples/intelligent_doctor/medical_materials_service/api"
	apiModel "github.com/ccnn-pcl/ccnn/app_examples/intelligent_doctor/medical_materials_service/api/model"
	"github.com/ccnn-pcl/ccnn/app_examples/intelligent_doctor/medical_materials_service/logger"

	"github.com/google/jsonschema-go/jsonschema"
	"github.com/modelcontextprotocol/go-sdk/mcp"
)

func init() {
	in, err := jsonschema.For[apiModel.DownloadCheckImageFileRequest](&jsonschema.ForOptions{})
	if err != nil {
		logger.Log.Fatal(err)
	}

	registerTool(MCPTool[*apiModel.DownloadCheckImageFileRequest, *apiModel.DownloadCheckImageFileResponse]{
		Name:        "checkimages",
		Description: "下载就诊时所使用的医学影像图片",
		In:          in,
		Out:         nil,
		Handler: func(ctx context.Context, request *mcp.CallToolRequest, in *apiModel.DownloadCheckImageFileRequest) (*mcp.CallToolResult, *apiModel.DownloadCheckImageFileResponse, error) {
			logger.Log.Infof("get one download check image mcp tool call for user %v", in)

			result, err := runCheckimagesTool(ctx, in)
			if err != nil {
				logger.Log.Errorf("run download chekc image tool for user %s error %v", in.UserID, err)
				return nil, nil, err
			}

			maxOutputLen := base64.StdEncoding.EncodedLen(len(result.Content))
			buf := make([]byte, maxOutputLen)
			base64.StdEncoding.Encode(buf, result.Content)

			logger.Log.Infof("get need download check image info for user %s, file %s size %d md5sum %s",
				in.UserID, result.FileName, result.FileSize, result.Md5sum)
			return &mcp.CallToolResult{
				Content: []mcp.Content{
					&mcp.ImageContent{
						MIMEType: result.MIMEType,
						Data:     result.Content,
						Meta: mcp.Meta{
							"id":          result.ID,
							"file_type":   result.FileType,
							"file_name":   result.FileName,
							"file_size":   result.FileSize,
							"file_md5sum": result.Md5sum,
						},
					},
				},
			}, nil, nil
		},
	})
}

// your logic goes here
func runCheckimagesTool(ctx context.Context, args *apiModel.DownloadCheckImageFileRequest) (*apiModel.DownloadCheckImageFileResponse, error) {
	// Implement your logic here
	return handler.DownloadChekImageFileHandler(ctx, args)
}
