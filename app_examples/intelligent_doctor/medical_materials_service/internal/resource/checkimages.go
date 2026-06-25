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

package resource

import (
	"context"
	"fmt"

	handler "github.com/ccnn-pcl/ccnn/app_examples/intelligent_doctor/medical_materials_service/api"
	apiModel "github.com/ccnn-pcl/ccnn/app_examples/intelligent_doctor/medical_materials_service/api/model"
	"github.com/ccnn-pcl/ccnn/app_examples/intelligent_doctor/medical_materials_service/logger"

	"github.com/modelcontextprotocol/go-sdk/mcp"
	"github.com/yosida95/uritemplate/v3"
)

var checkimageURITmpl, _ = uritemplate.New("file://users/{user_id}/visits/{visit_id}/checkimage/{image_id}")

func AddResource(server *mcp.Server) {
	server.AddResourceTemplate(&mcp.ResourceTemplate{
		Name:        "checkimages download",
		URITemplate: checkimageURITmpl.Raw(),
		Description: "下载就诊时所使用的医学影像图片",
	}, checkimageResourceHandler)
}

func checkimageResourceHandler(ctx context.Context, req *mcp.ReadResourceRequest) (*mcp.ReadResourceResult, error) {
	uri := req.Params.URI

	logger.Log.Infof("get one check image resource %s", uri)

	match := checkimageURITmpl.Match(uri)
	if match == nil {
		return nil, fmt.Errorf("invalid resource uri %s", uri)
	}
	downloadReq := apiModel.DownloadCheckImageFileRequest{}

	downloadReq.UserID = match.Get("user_id").String()
	downloadReq.VisitID = match.Get("visit_id").String()
	downloadReq.ImageID = match.Get("image_id").String()

	result, err := handler.DownloadChekImageFileHandler(ctx, &downloadReq)
	if err != nil {
		return nil, err
	}
	logger.Log.Infof("get need download check image info for user %s, file %s size %d md5sum %s",
		downloadReq.UserID, result.FileName, result.FileSize, result.Md5sum)
	return &mcp.ReadResourceResult{
		Contents: []*mcp.ResourceContents{
			{
				URI:      uri,
				MIMEType: result.MIMEType,
				Blob:     result.Content,
				Meta: mcp.Meta{
					"id":          result.ID,
					"file_type":   result.FileType,
					"file_name":   result.FileName,
					"file_size":   result.FileSize,
					"file_md5sum": result.Md5sum,
				},
			},
		},
	}, nil
}
