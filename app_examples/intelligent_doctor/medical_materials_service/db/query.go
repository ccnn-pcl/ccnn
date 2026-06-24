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

package db

import (
	"context"
	"fmt"
	"time"

	"github.com/ccnn-pcl/ccnn/app_examples/intelligent_doctor/medical_materials_service/db/model"
)

func QueryPatientVisitInfo(ctx context.Context, userID string, illnessKeyWord string, department string, startTime time.Time) ([]model.Visit, error) {
	if userID == "" {
		return nil, fmt.Errorf("user ID must be set")
	}
	if ctx == nil {
		ctx = context.Background()
	}
	ctx, cancel := context.WithTimeout(ctx, DEFAULT_QUERY_TIMEOUT)
	defer cancel()

	var visits []model.Visit

	query := gDB.WithContext(ctx).Joins("JOIN patients ON patients.id = visits.patient_id").
		Where("patients.user_id = ?", userID)

	if !startTime.IsZero() {
		startStr := startTime.Format("2006-01-02")
		query.Where("visits.visit_time >= ?", startStr)
	}
	if illnessKeyWord != "" {
		query = query.Where("visits.present_illness LIKE ?", "%"+illnessKeyWord+"%")
	}
	if department != "" {
		query = query.Where("visits.department = ?", department)
	}
	result := query.Order("visits.visit_time DESC").
		Preload("Diagnoses").
		Preload("Prescriptions").
		Preload("Prescriptions.DrugItems").
		Preload("VisitChecks").
		Preload("VisitChecks.RoutineCheck").
		Preload("VisitChecks.RoutineCheck.Items").
		Preload("VisitChecks.ImageCheck").
		Preload("VisitChecks.ImageCheck.CheckFiles").
		Preload("SurgicalRecords").
		Select("visits.*").
		Find(&visits)
	return visits, result.Error
}

func QueryPatientVisitByID(ctx context.Context, userID string, visitID string) (*model.Visit, error) {
	if userID == "" || visitID == "" {
		return nil, fmt.Errorf("user ID and visit ID must be set")
	}
	if ctx == nil {
		ctx = context.Background()
	}
	ctx, cancel := context.WithTimeout(ctx, DEFAULT_QUERY_TIMEOUT)
	defer cancel()

	visit := model.Visit{}

	query := gDB.WithContext(ctx).Joins("JOIN patients ON patients.id = visits.patient_id").
		Where("patients.user_id = ?", userID).
		Where("visits.id = ?", visitID)
	result := query.Order("visits.visit_time DESC").
		Preload("Diagnoses").
		Preload("Prescriptions").
		Preload("Prescriptions.DrugItems").
		Preload("VisitChecks").
		Preload("VisitChecks.RoutineCheck").
		Preload("VisitChecks.RoutineCheck.Items").
		Preload("VisitChecks.ImageCheck").
		Preload("VisitChecks.ImageCheck.CheckFiles").
		Select("visits.*").
		Take(&visit)
	if result.Error != nil {
		return nil, result.Error
	}
	return &visit, nil
}

func QueryPatientProfileByUserID(ctx context.Context, userID string) (*model.Patient, error) {
	if userID == "" {
		return nil, fmt.Errorf("user ID must be set")
	}
	if ctx == nil {
		ctx = context.Background()
	}
	patient := model.Patient{}

	ctx, cancel := context.WithTimeout(ctx, DEFAULT_QUERY_TIMEOUT)
	defer cancel()

	result := gDB.WithContext(ctx).Where("user_id = ?", userID).Take(&patient)
	if result.Error != nil {
		return nil, result.Error
	}
	return &patient, nil
}

func QueryVisitCheckInfo(ctx context.Context, visitID string) ([]model.VisitCheck, error) {
	if visitID == "" {
		return []model.VisitCheck{}, nil
	}

	if ctx == nil {
		ctx = context.Background()
	}
	ctx, cancel := context.WithTimeout(ctx, DEFAULT_QUERY_TIMEOUT)
	defer cancel()

	var checks []model.VisitCheck
	err := gDB.WithContext(ctx).Where("visit_id = ?", visitID).
		Preload("RoutineCheck").
		Preload("RoutineCheck.Items").
		Preload("ImageCheck").
		Preload("ImageCheck.CheckFiles").
		Order("check_time DESC").
		Find(&checks).Error
	return checks, err
}
