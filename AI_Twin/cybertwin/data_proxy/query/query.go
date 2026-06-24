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

package query

import (
	"github.com/ccnn-pcl/ccnn/AI_Twin/cybertwin/data_proxy/db"
	"gorm.io/gorm"
)

type MedicalDataQuery struct {
	db *gorm.DB
}

func NewMedicalDataQuery() *MedicalDataQuery {
	return &MedicalDataQuery{
		db: db.GetDB(),
	}
}

// 4种查询方法：
// - GetUserMedicalData(userID) → []MedicalDataStorage
// - GetUserBasicInfo(userID) → *User
// - GetMedicalDataByHospital(userID, hospitalID) → *MedicalDataStorage
// - GetAllUsersWithMedicalData() → []User

// GetUserMedicalData 获取用户的所有医疗数据存储信息
func (q *MedicalDataQuery) GetUserMedicalData(userID string) ([]db.MedicalDataStorage, error) {
	var medicalData []db.MedicalDataStorage

	err := q.db.Where("user_id = ? AND is_active = ?", userID, 1).
		Find(&medicalData).Error
	if err != nil {
		return nil, err
	}

	return medicalData, nil
}

// GetMedicalDataByHospital 根据医院ID获取医疗数据
func (q *MedicalDataQuery) GetMedicalDataByHospital(userID, department string) ([]db.MedicalDataStorage, error) {
	var medicalDatas []db.MedicalDataStorage
	err := q.db.Where("user_id = ? AND department = ? AND is_active = ?",
		userID, department, 1).Find(&medicalDatas).Error
	if err != nil {
		return nil, err
	}
	return medicalDatas, nil
}
