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
	"context"
	"fmt"
	"io"
	"mime"
	"path/filepath"
	"slices"
	"strings"
	"time"

	"github.com/ccnn-pcl/ccnn/app_examples/intelligent_doctor/medical_materials_service/api/model"
	dbModel "github.com/ccnn-pcl/ccnn/app_examples/intelligent_doctor/medical_materials_service/db/model"
	"github.com/ccnn-pcl/ccnn/app_examples/intelligent_doctor/medical_materials_service/logger"
	"github.com/gabriel-vasile/mimetype"
	"github.com/minio/minio-go/v7"
)

const DEFAULT_DOWNLOAD_RETRT_TIME int = 3

func convertToQueryVisitsInfoResponse(userID string, res []dbModel.Visit) *model.QueryVisitsInfoResponse {
	result := make([]model.Visit, 0, len(res))
	for _, v := range res {
		item := model.Visit{
			ID:         v.ID,
			PatientID:  v.PatientID,
			Hospital:   v.Hospital,
			VisitType:  v.VisitType,
			Department: v.Department,
			DoctorID:   v.DoctorID,
			VisitTime:  v.VisitTime,

			ChiefComplaint: v.ChiefComplaint,
			PresentIllness: v.PresentIllness,
			AuxiliaryExam:  v.AuxiliaryExam,
			TreatmentPlan:  v.TreatmentPlan,
		}
		if v.Diagnoses != nil {
			for _, d := range v.Diagnoses {
				item.Diagnoses = append(item.Diagnoses, model.Diagnosis{
					DiseaseName: d.DiseaseName,
					IsMain:      d.IsMain,
				})
			}
		}

		if v.Prescriptions != nil {
			for _, p := range v.Prescriptions {
				pre := model.Prescription{
					PrescribeTime: p.PrescribeTime,
					DrugType:      p.DrugType,
				}
				for _, drug := range p.DrugItems {
					pre.DrugItems = append(pre.DrugItems, model.PrescriptionDrug{
						DrugName:       drug.DrugName,
						Specification:  drug.Specification,
						Dosage:         drug.Dosage,
						Frequency:      drug.Frequency,
						Course:         drug.Course,
						TotalQuantity:  drug.TotalQuantity,
						Administration: drug.Administration,
					})
				}
				item.Prescriptions = append(item.Prescriptions, pre)
			}
		}

		if v.VisitChecks != nil {
			for _, check := range v.VisitChecks {
				c := model.VisitCheck{
					ID:          check.ID,
					CheckType:   check.CheckType,
					ApplyTime:   check.ApplyTime,
					ApplyDoctor: check.ApplyDoctor,
					CheckTime:   check.CheckTime,
					ReportTime:  check.ReportTime,
				}

				if check.RoutineCheck != nil {
					rc := model.RoutineCheck{
						Conclusion:  check.RoutineCheck.Conclusion,
						Interpreter: check.RoutineCheck.Interpreter,
					}
					for _, ci := range check.RoutineCheck.Items {
						rc.Items = append(rc.Items, model.RoutineCheckItem{
							IndicatorCode:  ci.IndicatorCode,
							IndicatorName:  ci.IndicatorName,
							Value:          ci.Value,
							ReferenceRange: ci.ReferenceRange,
							AbnormalFlag:   ci.AbnormalFlag,
						})
					}
					c.RoutineCheck = &rc
				}

				if check.ImageCheck != nil {
					ic := model.ImageCheck{
						Conclusion:  check.ImageCheck.Conclusion,
						Interpreter: check.ImageCheck.Interpreter,
					}
					for _, icf := range check.ImageCheck.CheckFiles {
						ic.CheckFiles = append(ic.CheckFiles, model.CheckFile{
							ID:          icf.ID,
							Filename:    icf.Filename,
							FileType:    icf.FileType,
							FileSize:    icf.FileSize,
							FileMd5sum:  icf.FileMd5sum,
							StoragePath: icf.StoragePath,
							Description: icf.Description,
							UploadTime:  icf.UploadTime,
						})
					}
					c.ImageCheck = &ic
				}
				item.VisitChecks = append(item.VisitChecks, c)
			}
		}

		result = append(result, item)
	}
	return &model.QueryVisitsInfoResponse{
		UserID: userID,
		Visits: result,
	}
}

// detectMimeType tries to determine the MIME type of a file
func detectMimeType(r io.Reader) string {
	// Use mimetype library for more accurate detection
	mtype, err := mimetype.DetectReader(r)
	if err != nil {
		return "application/octet-stream" // Default
	}

	return mtype.String()
}

// isTextFile determines if a file is likely a text file based on MIME type
func isTextFile(mimeType string) bool {
	// Check for common text MIME types
	if strings.HasPrefix(mimeType, "text/") {
		return true
	}

	// Common application types that are text-based
	textApplicationTypes := []string{
		"application/json",
		"application/xml",
		"application/javascript",
		"application/x-javascript",
		"application/typescript",
		"application/x-typescript",
		"application/x-yaml",
		"application/yaml",
		"application/toml",
		"application/x-sh",
		"application/x-shellscript",
	}

	if slices.Contains(textApplicationTypes, mimeType) {
		return true
	}

	// Check for +format types
	if strings.Contains(mimeType, "+xml") ||
		strings.Contains(mimeType, "+json") ||
		strings.Contains(mimeType, "+yaml") {
		return true
	}

	// Common code file types that might be misidentified
	if strings.HasPrefix(mimeType, "text/x-") {
		return true
	}

	if strings.HasPrefix(mimeType, "application/x-") &&
		(strings.Contains(mimeType, "script") ||
			strings.Contains(mimeType, "source") ||
			strings.Contains(mimeType, "code")) {
		return true
	}

	return false
}

// isImageFile determines if a file is an image based on MIME type
func isImageFile(mimeType string) bool {
	return strings.HasPrefix(mimeType, "image/") || strings.HasSuffix(mimeType, "octet-stream") ||
		(mimeType == "application/xml" && strings.HasSuffix(strings.ToLower(mimeType), ".svg"))
}

// detectMimeType tries to determine the MIME type of a file
func detectMimeTypeByPath(path string) string {
	// Use mimetype library for more accurate detection
	mtype, err := mimetype.DetectFile(path)
	if err != nil {
		// Fallback to extension-based detection if file can't be read
		ext := filepath.Ext(path)
		if ext != "" {
			mimeType := mime.TypeByExtension(ext)
			if mimeType != "" {
				return mimeType
			}
		}
		return "application/octet-stream" // Default
	}

	return mtype.String()
}

func downloadImageFromOBS(ctx context.Context, client *minio.Client, bucket string, objectKey string, retry int, w io.Writer) (int64, error) {
	if retry == 0 {
		retry = DEFAULT_DOWNLOAD_RETRT_TIME
	}
	for i := 0; i < retry; i++ {
		opts := minio.GetObjectOptions{}

		obj, err := client.GetObject(ctx, bucket, objectKey, opts)
		if err != nil {
			logger.Log.Errorf("retry %d download bucket %s object %s error: %v", i, bucket, objectKey, err)
			time.Sleep(time.Second * time.Duration(i+1)) // 指数退避重试
			continue
		}

		size, err := io.Copy(w, obj)
		obj.Close()
		if err != nil {
			logger.Log.Errorf("retry %d copy bucket %s object %s to writer error: %v", i, bucket, objectKey, err)
			time.Sleep(time.Second * time.Duration(i+1)) // 指数退避重试
			continue
		}
		logger.Log.Infof("download bucket %s object %s success, size: %d", bucket, objectKey, size)
		return size, nil

	}
	return 0, fmt.Errorf("download bucket %s object %s had try %d time, and still failure", bucket, objectKey, retry)
}

func convertToQueryPatientMedicalInfoResoponse(profile *dbModel.Patient, visits []dbModel.Visit) *model.QueryPatientMedicalInfoResponse {
	res := model.QueryPatientMedicalInfoResponse{}

	// 病史数据
	res.MedicalData.MedicalHistory.ChronicDiseases = profile.MedicalHistory
	res.MedicalData.MedicalHistory.FamilyHistory = profile.FamilyMedicalHistory
	res.MedicalData.MedicalHistory.Allergies = profile.AllergyHistory
	res.MedicalData.MedicalHistory.PreviousConditions = []model.PreviousCondition{}
	res.MedicalData.MedicalHistory.LastUpdate = &profile.UpdatedAt

	medications := []model.Medication{}
	labResults := []model.LabResult{}
	ImageingDatas := []model.ImageingData{}

	surgicalRecords := []model.SurgicalRecord{}
	sources := make(map[string]struct{})

	for _, v := range visits {
		sources[v.Hospital] = struct{}{}

		medications = append(medications, convertMedications(v.Hospital, v.Prescriptions)...)
		l, c := convertCheck(v.Hospital, v.VisitChecks)
		labResults = append(labResults, l...)
		ImageingDatas = append(ImageingDatas, c...)
		surgicalRecords = append(surgicalRecords, convertSugicalRecords(v.Hospital, v.SurgicalRecords)...)
	}

	res.MedicalData.LabResults = labResults
	res.MedicalData.ImageingData = ImageingDatas
	res.MedicalData.Medications = medications
	for k := range sources {
		res.MedicalData.Source = append(res.MedicalData.Source, k)
	}
	return &res
}

func convertMedications(hospital string, p []dbModel.Prescription) []model.Medication {
	m := []model.Medication{}

	for _, prescrition := range p {
		for _, drug := range prescrition.DrugItems {
			m = append(m, model.Medication{
				MedicationName: drug.DrugName,
				Dosage:         drug.Dosage,
				Course:         drug.Course,
				Frequency:      drug.Frequency,
				StartDate:      prescrition.PrescribeTime.Format("2006-01-02"),
				Purpose:        drug.Purpose,
				Hospital:       hospital,
			})
		}
	}
	return m
}

func convertCheck(hospital string, c []dbModel.VisitCheck) ([]model.LabResult, []model.ImageingData) {
	labs := []model.LabResult{}
	images := []model.ImageingData{}
	for _, check := range c {
		if check.CheckType == dbModel.ROUTINE_VISIT_CHECK_TYPE {
			for _, lab := range check.RoutineCheck.Items {
				labs = append(labs, model.LabResult{
					TestName:       lab.IndicatorName,
					Result:         lab.Value,
					ReferenceRange: lab.ReferenceRange,
					Status:         lab.AbnormalFlag,
					TestDate:       check.CheckTime.Format("2006-01-02"),
					Hospital:       hospital,
				})
			}
		} else {
			for _, image := range check.ImageCheck.CheckFiles {
				images = append(images, model.ImageingData{
					ImMagingID:      image.ID,
					ImagingType:     image.FileType,
					ExaminationDate: check.CheckTime.Format("2006-01-02"),
					Conclusion:      check.RoutineCheck.Conclusion,
					Findings:        image.Description,
					Hospital:        hospital,
					ImageUrl:        image.StoragePath,
				})
			}
		}
	}
	return labs, images
}

func convertSugicalRecords(hospital string, s []dbModel.SurgicalRecord) []model.SurgicalRecord {
	records := []model.SurgicalRecord{}
	for _, r := range s {
		records = append(records, model.SurgicalRecord{
			SurgeryName: r.SurgicalName,
			SurgeryDate: r.SurgicalDate.Format("2006-01-02"),
			Surgeon:     r.Surgeon,
			Status:      r.SurgicalResult,
			Hospital:    hospital,
		})
	}
	return records
}
