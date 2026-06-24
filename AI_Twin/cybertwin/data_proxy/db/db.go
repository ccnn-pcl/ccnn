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
	"fmt"
	"time"

	"github.com/ccnn-pcl/ccnn/AI_Twin/cybertwin/data_proxy/config"
	l "github.com/ccnn-pcl/ccnn/AI_Twin/cybertwin/data_proxy/logger"
	"github.com/sirupsen/logrus"
	"gorm.io/driver/mysql"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
	"gorm.io/plugin/dbresolver"
)

var gDB *gorm.DB

const DEFAULT_QUERY_TIMEOUT time.Duration = 5 * time.Second

var dsnFormater = "%s:%s@tcp(%s)/%s?charset=utf8mb4&parseTime=True&loc=Local&timeout=%ds&readTimeout=%ds&writeTimeout=%ds"

func validAndFixConfig(dbConfig *config.DBConfig) error {
	if dbConfig == nil {
		return fmt.Errorf("db config is nil")
	}

	if len(dbConfig.Addresses) == 0 {
		return fmt.Errorf("address is empty")
	}

	if dbConfig.Password == "" || dbConfig.User == "" {
		return fmt.Errorf("db user or pw is empty")
	}

	if dbConfig.DBName == "" {
		dbConfig.DBName = "medical_db"
	}

	if dbConfig.TimeoutConfig.ConnTimeout <= 0 {
		dbConfig.TimeoutConfig.ConnTimeout = 10
	}
	if dbConfig.TimeoutConfig.ReadTimeout <= 0 {
		dbConfig.TimeoutConfig.ReadTimeout = 30
	}

	if dbConfig.TimeoutConfig.WriteTimeout <= 0 {
		dbConfig.TimeoutConfig.WriteTimeout = 30
	}

	if dbConfig.TimeoutConfig.OpTimeout <= 0 {
		dbConfig.TimeoutConfig.OpTimeout = 30
	}

	if dbConfig.PoolConfig.MaxOpenConns <= 0 {
		dbConfig.PoolConfig.MaxOpenConns = 1000
	}

	if dbConfig.PoolConfig.MaxIdleConns <= 0 {
		dbConfig.PoolConfig.MaxIdleConns = dbConfig.PoolConfig.MaxOpenConns / 5
	}

	if dbConfig.PoolConfig.ConnMaxLifetime <= 0 {
		dbConfig.PoolConfig.ConnMaxLifetime = 3600
	}
	if dbConfig.PoolConfig.ConnMaxIdletime <= 0 {
		dbConfig.PoolConfig.ConnMaxIdletime = 30 * 60
	}
	return nil
}

func InitDB(dbConfig *config.DBConfig) error {
	if err := validAndFixConfig(dbConfig); err != nil {
		l.Log.Errorf("init db config invalid %v", err)
		return err
	}

	newLogger := logger.New(
		l.Log.WithFields(logrus.Fields{
			"module":    "db",
			"addresses": dbConfig.Addresses,
		}),
		logger.Config{
			SlowThreshold:             1 * time.Second, // Slow SQL threshold
			LogLevel:                  logger.Info,     // Log level
			IgnoreRecordNotFoundError: false,           // Ignore ErrRecordNotFound error for logger
			ParameterizedQueries:      false,           // Don't include params in the SQL log
			Colorful:                  true,            // Disable color
		})

	gormConfig := &gorm.Config{
		Logger: newLogger,
	}

	if dbConfig.SSL.Enable {
		dsnFormater += "&tls=true&sslca=" + dbConfig.SSL.CAFile + "&sslcert=" + dbConfig.SSL.CertFile + "&sslkey=" + dbConfig.SSL.KeyFile
	}

	// 解析主库配置
	var masterDBs []gorm.Dialector
	for _, addr := range dbConfig.Addresses {
		dsn_str := fmt.Sprintf(dsnFormater, dbConfig.User, dbConfig.Password, addr, dbConfig.DBName,
			dbConfig.TimeoutConfig.ConnTimeout, dbConfig.TimeoutConfig.ReadTimeout, dbConfig.TimeoutConfig.WriteTimeout)

		fmt.Printf("dsn: %v", dsn_str)
		masterDBs = append(masterDBs, mysql.Open(dsn_str))
	}
	// 初始化主库连接
	mainDB, err := gorm.Open(masterDBs[0], gormConfig)
	if err != nil {
		return fmt.Errorf("connect master db error: %v", err)
	}
	// 配置DBResolver
	resolver := dbresolver.Register(dbresolver.Config{
		Sources: masterDBs,                 // 主库列表
		Policy:  dbresolver.RandomPolicy{}, // 负载均衡策略: 随机
	})
	// 注册插件
	if err := mainDB.Use(resolver); err != nil {
		return fmt.Errorf("register DBResolver failure: %v", err)
	}
	// 设置连接池参数
	sqlDB, err := mainDB.DB()
	if err != nil {
		return fmt.Errorf("get SQL DB error: %v", err)
	}
	sqlDB.SetMaxOpenConns(dbConfig.PoolConfig.MaxOpenConns)
	sqlDB.SetMaxIdleConns(dbConfig.PoolConfig.MaxIdleConns)
	sqlDB.SetConnMaxLifetime(time.Duration(dbConfig.PoolConfig.ConnMaxLifetime) * time.Second)
	sqlDB.SetConnMaxIdleTime(time.Duration(dbConfig.PoolConfig.ConnMaxIdletime) * time.Second)
	// 创建表
	if err := mainDB.AutoMigrate(
		&MedicalDataStorage{},
	); err != nil {
		l.Log.Errorf("auto migrate table error: %v, ignore it", err)
	}

	gDB = mainDB
	l.Log.Info("init db success")

	return nil
}

func GetDB() *gorm.DB {
	return gDB
}
