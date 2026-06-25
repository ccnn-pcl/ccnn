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

package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"

	verifier "github.com/ccnn-pcl/ccnn/app_examples/intelligent_doctor/medical_materials_service/auth"
	"github.com/ccnn-pcl/ccnn/app_examples/intelligent_doctor/medical_materials_service/config"
	"github.com/ccnn-pcl/ccnn/app_examples/intelligent_doctor/medical_materials_service/db"
	"github.com/ccnn-pcl/ccnn/app_examples/intelligent_doctor/medical_materials_service/internal/resource"
	"github.com/ccnn-pcl/ccnn/app_examples/intelligent_doctor/medical_materials_service/internal/tools"
	"github.com/ccnn-pcl/ccnn/app_examples/intelligent_doctor/medical_materials_service/logger"
	"github.com/modelcontextprotocol/go-sdk/auth"
	"github.com/modelcontextprotocol/go-sdk/mcp"
)

var (
	versionFlag = flag.Bool("version", false, "显示版本信息")
)

func main() {
	flag.Parse()

	// 如果指定了--version标志，显示版本信息并退出
	if *versionFlag {
		fmt.Println(config.PrintVersion())
		os.Exit(0)
	}

	if err := run(); err != nil {
		fmt.Fprintf(os.Stderr, "error: %v\n", err)
		os.Exit(1)
	}
}

func run() error {
	// init config
	if err := config.InitConfig(); err != nil {
		log.Fatalf("init config error %v", err)
		return err
	}

	// init logger
	logConfig := config.GetLogConfig()
	if err := logger.InitLogger(logConfig.FilePath, logConfig.Verbose, logConfig.Debug, nil); err != nil {
		log.Fatalf("init logger error %v", err)
		return err
	}
	// init db
	if err := db.InitDB(config.GetDBConfig()); err != nil {
		log.Fatalf("init db error %v", err)
		return err
	}

	// Create the MCP server
	logger.Log.Info("start to create mcp server")
	server := mcp.NewServer(&mcp.Implementation{Name: "MedicalMaterialsMcpService", Version: config.Version}, nil)

	// Register tools
	tools.AddToolsToServer(server)

	// Add Resrouces
	resource.AddResource(server)

	serverConfig := config.GetServerConfig()

	// Start server with appropriate transport
	if serverConfig.Address != "" {
		authHandlerMiddleware := auth.RequireBearerToken(verifier.Verify, &auth.RequireBearerTokenOptions{
			Scopes: []string{"read"},
		})

		handler := mcp.NewStreamableHTTPHandler(func(*http.Request) *mcp.Server {
			return server
		}, nil)
		logger.Log.Infof("MCP server listening at %s", serverConfig.Address)
		return http.ListenAndServe(serverConfig.Address, authHandlerMiddleware(handler))
	} else {
		t := &mcp.LoggingTransport{Transport: &mcp.StdioTransport{}, Writer: os.Stderr}
		return server.Run(context.Background(), t)
	}
}
