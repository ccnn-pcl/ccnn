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

package api

import (
	"bytes"
	"context"
	"crypto/md5"
	"encoding/hex"
	"fmt"
	"io"
	"net/url"
	"strings"
	"time"

	"github.com/ccnn-pcl/ccnn/app_examples/intelligent_doctor/medical_materials_service/api/model"
	"github.com/ccnn-pcl/ccnn/app_examples/intelligent_doctor/medical_materials_service/config"
	"github.com/ccnn-pcl/ccnn/app_examples/intelligent_doctor/medical_materials_service/db"
	dbmodel "github.com/ccnn-pcl/ccnn/app_examples/intelligent_doctor/medical_materials_service/db/model"
	"github.com/ccnn-pcl/ccnn/app_examples/intelligent_doctor/medical_materials_service/logger"
	"github.com/minio/minio-go/v7"
	"github.com/minio/minio-go/v7/pkg/credentials"
	"github.com/modelcontextprotocol/go-sdk/auth"
)

func QueryVisitsInfoHandler(ctx context.Context, req *model.QueryVisitsInfoRequest) (*model.QueryVisitsInfoResponse, error) {
	if req == nil {
		logger.Log.Errorf("invalid query parameter, is nill")
		return nil, fmt.Errorf("invalid query parameter")
	}
	logger.Log.Infof("start to handle query visits info request for %v", *req)

	if req.UserID == "" {
		err := fmt.Errorf("user id is empty")
		logger.Log.Errorln(err)
		return nil, err
	}

	if req.StartTime == "" {
		req.StartTime = time.Now().AddDate(-1, 0, 0).Format("2006-01-02 15:04:05")
	}

	startTime, err := time.Parse("2006-01-02", req.StartTime)
	if err != nil {
		logger.Log.Errorf("start time formater is invalid %s", req.StartTime)
		startTime = time.Now().AddDate(-1, 0, 0)
	}

	result, err := db.QueryPatientVisitInfo(ctx, req.UserID, req.IllnessKeyWord, req.Department, startTime)
	if err != nil {
		logger.Log.Errorf("query patient visit info for user %s from db error %v", req.UserID, err)
		return nil, err
	}
	logger.Log.Infof("query visits info for user %s succes, count %d", req.UserID, len(result))
	return convertToQueryVisitsInfoResponse(req.UserID, result), nil
}

func DownloadChekImageFileHandler(ctx context.Context, req *model.DownloadCheckImageFileRequest) (*model.DownloadCheckImageFileResponse, error) {
	if req == nil {
		logger.Log.Errorf("invalid query parameter, is nill")
		return nil, fmt.Errorf("invalid query parameter")
	}
	logger.Log.Infof("start to handle download check image request for %v", *req)

	if req.UserID == "" || req.VisitID == "" {
		err := fmt.Errorf("user id or visit id is empty")
		logger.Log.Errorln(err)
		return nil, err
	}

	if req.ImageID == "" {
		err := fmt.Errorf("check image id is empty")
		logger.Log.Errorln(err)
		return nil, err
	}

	visitInfo, err := db.QueryPatientVisitByID(ctx, req.UserID, req.VisitID)
	if err != nil {
		logger.Log.Errorf("query visit info by %s from db error %v", req.VisitID, err)
		return nil, err
	}
	var imageInfo dbmodel.CheckFile
	found := false
	for _, check := range visitInfo.VisitChecks {
		if check.CheckType != dbmodel.IMAGE_VISIT_CHECK_TYPE {
			continue
		}
		for _, file := range check.ImageCheck.CheckFiles {
			if file.ID == req.ImageID {
				imageInfo = file
				found = true
				break
			}
		}
	}
	if !found {
		err := fmt.Errorf("check image %s is no found for visit %s", req.ImageID, req.VisitID)
		logger.Log.Errorln(err)
		return nil, err
	}
	obsURLStr := imageInfo.StoragePath
	if obsURLStr == "" {
		err := fmt.Errorf("image %s storage path is empty", imageInfo.Filename)
		logger.Log.Errorln(err)
		return nil, err
	}

	obsURL, err := url.Parse(obsURLStr)
	if err != nil {
		logger.Log.Errorf("image %s had invalid obs_url: %s error: %v", req.ImageID, obsURLStr, err)
		return nil, fmt.Errorf("image %s had invalid obs_url: %s error: %v",
			req.ImageID, obsURLStr, err)
	}

	// OBS URL 路径格式通常为: /bucket/object-key，分割出 bucket 和 object
	pathParts := strings.Split(strings.Trim(obsURL.Path, "/"), "/")
	if len(pathParts) < 1 {
		logger.Log.Errorf("image %s invalid 'obs_url' path %s", req.ImageID, obsURLStr)
		return nil, fmt.Errorf("invalid obs url in db")
	}
	bucket := pathParts[0]
	objectKey := strings.Join(pathParts[1:], "/")
	useSSL := obsURL.Scheme == "https"

	endpoint := obsURL.Host
	if endpoint != config.GetObsAuthConfig().Endpoint {
		logger.Log.Errorf("no ak/sk for obs host %s at config", endpoint)
		return nil, fmt.Errorf("no ak/sk for obs host %s", endpoint)
	}

	accessKey := config.GetObsAuthConfig().AccessKey
	secretKey := config.GetObsAuthConfig().SecretKey
	minioClient, err := minio.New(endpoint, &minio.Options{
		Creds:  credentials.NewStaticV4(accessKey, secretKey, ""),
		Secure: useSSL,
	})
	if err != nil {
		logger.Log.Errorf("create obs client error %v", err)
		return nil, err
	}

	// 获取 OBS 对象的元信息
	objInfo, err := minioClient.StatObject(ctx, bucket, objectKey, minio.StatObjectOptions{})
	if err != nil {
		err = fmt.Errorf("failed to stat OBS object %s:%s error: %v ", bucket, objectKey, err)
		logger.Log.Errorln(err)
		return nil, err
	}
	md5Hash := md5.New()
	buf := bytes.NewBuffer(nil)
	writer := io.MultiWriter(md5Hash, buf)

	downloadSize, err := downloadImageFromOBS(ctx, minioClient, bucket, objectKey, 3, writer)
	if err != nil {
		logger.Log.Errorf("failed to download OBS object %s:%s error: %v ", bucket, objectKey, err)
		return nil, err
	}
	logger.Log.Infof("dowland object %s size %d", objectKey, downloadSize)
	if downloadSize != objInfo.Size {
		err := fmt.Errorf("dowland size %d is not eq to object metadata size %d", downloadSize, objInfo.Size)
		logger.Log.Errorln(err)
		return nil, err
	}
	if downloadSize != imageInfo.FileSize {
		err := fmt.Errorf("download file size %d is not eq to db record %d", downloadSize, imageInfo.FileSize)
		logger.Log.Errorln(err)
		return nil, err
	}
	curMd5Str := hex.EncodeToString(md5Hash.Sum(nil))
	if !strings.EqualFold(imageInfo.FileMd5sum, curMd5Str) {
		err := fmt.Errorf("check md5sum error, file maybe be changed, %s - %s", imageInfo.FileMd5sum, curMd5Str)
		logger.Log.Errorln(err)
		return nil, err
	}
	mimeType := objInfo.ContentType
	if mimeType == "" {
		mimeType = detectMimeType(buf)
	}
	if !isImageFile(mimeType) {
		err := fmt.Errorf("file minetype is no image %s - %s", objectKey, mimeType)
		logger.Log.Errorln(err)
		return nil, err

	}
	logger.Log.Infof("dowland object %s size %d sucess", objectKey, downloadSize)
	return &model.DownloadCheckImageFileResponse{
		ID:       imageInfo.ID,
		Md5sum:   imageInfo.FileMd5sum,
		FileType: imageInfo.FileType,
		FileName: imageInfo.Filename,
		FileSize: uint64(imageInfo.FileSize),
		Content:  buf.Bytes(),
		MIMEType: mimeType,
	}, nil
}

func QueryPatientProfileHandler(ctx context.Context, req *model.QueryPatientProfileRequest) (*model.QueryPatientProfileResponse, error) {
	if req == nil {
		logger.Log.Errorf("invalid query parameter, is nill")
		return nil, fmt.Errorf("invalid query parameter")
	}
	logger.Log.Infof("start to handle query patient profile info request for %v", *req)

	if req.UserID == "" {
		err := fmt.Errorf("user id is empty")
		logger.Log.Errorln(err)
		return nil, err
	}

	profile, err := db.QueryPatientProfileByUserID(ctx, req.UserID)
	if err != nil || profile == nil {
		logger.Log.Errorf("query patient profile from db error %v", err)
		return nil, err
	}

	logger.Log.Infof("handle query patient profile info request for %v success %v", *req, profile)
	return &model.QueryPatientProfileResponse{
		ID:               profile.ID,
		UserID:           profile.UserID,
		MedicalRecordNo:  profile.MedicalRecordNo,
		Name:             profile.Name,
		Gender:           profile.Gender,
		Birthday:         profile.Birthday.Format("2006-01-02"),
		IDCard:           profile.IDCard,
		Phone:            profile.Phone,
		Address:          profile.Address,
		AllergyHistory:   profile.AllergyHistory,
		MedicalHistory:   profile.MedicalHistory,
		EmergencyContact: profile.EmergencyContact,
		EmergencyPhone:   profile.EmergencyContact,
	}, nil
}

func QueryPatientMedicalInfoHandler(ctx context.Context, req *model.QueryPatientMedicalInfoRequest) (*model.QueryPatientMedicalInfoResponse, error) {
	l := logger.Log.WithField("request_id", req.RequestID)
	if req == nil {
		l.Errorf("invalid query parameter, is nill")
		return nil, fmt.Errorf("invalid query parameter")
	}
	jwt := auth.TokenInfoFromContext(ctx)
	if jwt == nil {
		err := fmt.Errorf("can no found token error")
		l.Error(err)
		return nil, err
	}
	l.Infof("start to handle query visits info request for %v, token %v", *req, jwt.Expiration)
	if jwt.Extra["user_id"] != req.UserID || jwt.Extra["department"] != req.Department {
		l.Errorf("user id %s or department %s is invalid for token info %v", req.UserID, req.Department, jwt.Extra)
		return nil, fmt.Errorf("invalid token")
	}

	if req.UserID == "" {
		err := fmt.Errorf("user id is empty")
		logger.Log.Errorln(err)
		return nil, err
	}
	startTime := time.Time{}
	var err error
	if req.StartTime != "" {
		startTime, err = time.Parse("2006-01-02", req.StartTime)
		if err != nil {
			l.Errorf("start time formater is invalid %s", req.StartTime)
			return nil, err
		}
	}
	profile, err := db.QueryPatientProfileByUserID(ctx, req.UserID)
	if err != nil {
		l.Errorf("query user %s profile error %v", req.UserID, err)
		return nil, err
	}
	l.Infof("get user id %s profile and medical reocrd no %s", req.UserID, profile.MedicalRecordNo)

	visits, err := db.QueryPatientVisitInfo(ctx, req.UserID, "", req.Department, startTime)
	if err != nil {
		l.Errorf("query patient visit info for user %s from db error %v", req.UserID, err)
		return nil, err
	}
	logger.Log.Infof("query visits info for user %s succes, count %d", req.UserID, len(visits))
	res := convertToQueryPatientMedicalInfoResoponse(profile, visits)
	res.RequestID = req.RequestID
	return res, nil
}
