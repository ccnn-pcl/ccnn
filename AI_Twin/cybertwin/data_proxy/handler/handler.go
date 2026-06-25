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

package handler

import (
	"context"

	"github.com/ccnn-pcl/ccnn/AI_Twin/cybertwin/data_proxy/logger"
	"github.com/ccnn-pcl/ccnn/AI_Twin/cybertwin/data_proxy/query"
)

type DataHandler struct {
	query *query.MedicalDataQuery
}

func NewDataHandler() *DataHandler {
	return &DataHandler{
		query: query.NewMedicalDataQuery(),
	}
}

// 请求结构体
type GetHospitalDataRequest struct {
	UserID     string `json:"user_id" binding:"required"`
	Department string `json:"department" binding:"department"`
}

// 响应结构体
type HospitalDataResponse struct {
	Datas []HospitalData `json:"datas"`
}

type HospitalData struct {
	Location           string `json:"hospital_location"`
	HospitalName       string `json:"hospital_name"`
	Department         string `json:"department"`
	DataServiceAddress string `json:"data_service_address"`
	DataTypes          string `json:"data_types"`
}

// GetHospitalMedicalData 获取特定医院的医疗数据信息
func (h *DataHandler) GetHospitalMedicalData(c context.Context, req *GetHospitalDataRequest) (*HospitalDataResponse, error) {
	medicalData, err := h.query.GetMedicalDataByHospital(req.UserID, req.Department)
	if err != nil {
		logger.Log.Errorf("Error getting hospital data for user %s, department %s: %v",
			req.UserID, req.Department, err)
		return nil, err
	}

	var datas []HospitalData
	for _, d := range medicalData {
		datas = append(datas, HospitalData{
			Location:           d.Location,
			HospitalName:       d.HospitalName,
			Department:         d.Department,
			DataServiceAddress: d.DataServiceAddress,
			DataTypes:          d.DataTypes,
		})
	}

	return &HospitalDataResponse{
		Datas: datas,
	}, nil
}
