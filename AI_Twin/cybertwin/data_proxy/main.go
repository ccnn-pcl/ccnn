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

	verifier "github.com/ccnn-pcl/ccnn/AI_Twin/cybertwin/data_proxy/auth"
	"github.com/ccnn-pcl/ccnn/AI_Twin/cybertwin/data_proxy/config"
	"github.com/ccnn-pcl/ccnn/AI_Twin/cybertwin/data_proxy/db"
	"github.com/ccnn-pcl/ccnn/AI_Twin/cybertwin/data_proxy/internal/tools"
	"github.com/ccnn-pcl/ccnn/AI_Twin/cybertwin/data_proxy/logger"
	"github.com/modelcontextprotocol/go-sdk/auth"
	"github.com/modelcontextprotocol/go-sdk/mcp"
)

// Command line flags
var (
	versionFlag   bool
	helpFlag      bool
	configPath    string
	address       string
	logLevel      string
)

func init() {
	// Parse command line flags
	flag.BoolVar(&versionFlag, "v", false, "Show version information")
	flag.BoolVar(&versionFlag, "version", false, "Show version information")
	flag.BoolVar(&helpFlag, "h", false, "Show help message")
	flag.BoolVar(&helpFlag, "help", false, "Show help message")
	flag.StringVar(&configPath, "c", "", "Path to configuration file (default: ./conf/config.yaml)")
	flag.StringVar(&configPath, "config", "", "Path to configuration file (default: ./conf/config.yaml)")
	flag.StringVar(&address, "a", "", "Server address to listen on (overrides config file)")
	flag.StringVar(&address, "address", "", "Server address to listen on (overrides config file)")
	flag.StringVar(&logLevel, "l", "info", "Log level (debug, info, warn, error)")
	flag.StringVar(&logLevel, "log-level", "info", "Log level (debug, info, warn, error)")
	
	flag.Usage = func() {
		printHelp()
	}
}

func main() {
	flag.Parse()

	// Handle version flag
	if versionFlag {
		fmt.Println(config.GetVersionString())
		os.Exit(0)
	}

	// Handle help flag
	if helpFlag {
		printHelp()
		os.Exit(0)
	}

	// Run the application
	if err := run(); err != nil {
		fmt.Fprintf(os.Stderr, "error: %v\n", err)
		os.Exit(1)
	}
}

func printHelp() {
	fmt.Println("Cybertwin DataProxy Service")
	fmt.Println("")
	fmt.Println("Usage:")
	fmt.Println("  server [options]")
	fmt.Println("")
	fmt.Println("Options:")
	fmt.Println("  -v, --version            Show version information")
	fmt.Println("  -h, --help               Show this help message")
	fmt.Println("  -c, --config <path>      Path to configuration file (default: ./conf/config.yaml)")
	fmt.Println("  -a, --address <addr>     Server address to listen on (overrides config file)")
	fmt.Println("  -l, --log-level <level>  Log level (debug, info, warn, error) (default: info)")
	fmt.Println("")
	fmt.Println("Description:")
	fmt.Println("  Cybertwin DataProxy Service provides data proxy functionality for Cybertwin platform.")
	fmt.Println("  It supports MCP (Model Context Protocol) for AI tool integration.")
	fmt.Println("")
	fmt.Println("Examples:")
	fmt.Println("  server -v                    Show version information")
	fmt.Println("  server --version             Show version information")
	fmt.Println("  server -h                    Show this help message")
	fmt.Println("  server --help                Show this help message")
	fmt.Println("  server                       Start the server with default configuration")
	fmt.Println("  server -a :8080              Start the server on port 8080")
	fmt.Println("  server -c /path/to/config.yaml  Use custom configuration file")
	fmt.Println("  server -l debug              Start with debug log level")
	fmt.Println("")
	fmt.Println("Configuration:")
	fmt.Println("  The service reads configuration from ./conf/config.yaml by default")
	fmt.Println("  See conf/config.yaml.example for configuration options")
	fmt.Println("")
	fmt.Println("Environment Variables:")
	fmt.Println("  CYBERTWIN_CONFIG_PATH    Path to configuration file")
	fmt.Println("  CYBERTWIN_LOG_LEVEL      Log level (debug, info, warn, error)")
	fmt.Println("  CYBERTWIN_SERVER_ADDRESS Server address to listen on")
}

func run() error {
	// Print version information on startup
	config.PrintVersion()

	// Set configuration path from command line or environment
	if configPath == "" {
		if envConfigPath := os.Getenv("CYBERTWIN_CONFIG_PATH"); envConfigPath != "" {
			configPath = envConfigPath
		}
	}

	// Set server address from command line or environment
	if address == "" {
		if envAddress := os.Getenv("CYBERTWIN_SERVER_ADDRESS"); envAddress != "" {
			address = envAddress
		}
	}

	// Set log level from command line or environment
	if logLevel == "info" {
		if envLogLevel := os.Getenv("CYBERTWIN_LOG_LEVEL"); envLogLevel != "" {
			logLevel = envLogLevel
		}
	}

	// init config with custom path if provided
	if configPath != "" {
		// Note: This would require modifying config.InitConfig to accept a path parameter
		// For now, we'll just log it
		log.Printf("Using custom config path: %s", configPath)
		// TODO: Implement config path override in config package
	}
	
	if err := config.InitConfig(); err != nil {
		log.Fatalf("init config error %v", err)
		return err
	}

	// Override server address if provided via command line
	if address != "" {
		// This would require modifying config package to set address
		log.Printf("Overriding server address to: %s", address)
		// TODO: Implement address override in config package
	}

	// init logger with log level
	logConfig := config.GetLogConfig()
	
	// Set debug/verbose based on log level
	switch logLevel {
	case "debug":
		logConfig.Debug = true
		logConfig.Verbose = true
	case "info":
		logConfig.Verbose = true
		logConfig.Debug = false
	case "warn", "error":
		logConfig.Verbose = false
		logConfig.Debug = false
	}
	
	if err := logger.InitLogger(logConfig.FilePath, logConfig.Verbose, logConfig.Debug, nil); err != nil {
		log.Fatalf("init logger error %v", err)
		return err
	}
	
	// Log startup information
	logger.Log.Infof("Starting Cybertwin DataProxy Service")
	logger.Log.Infof("Log level: %s", logLevel)
	if configPath != "" {
		logger.Log.Infof("Config path: %s", configPath)
	}
	if address != "" {
		logger.Log.Infof("Server address override: %s", address)
	}
	
	// init db
	if err := db.InitDB(config.GetDBConfig()); err != nil {
		logger.Log.Fatalf("init db error %v", err)
		return err
	}

	// Create the MCP server
	logger.Log.Info("start to create mcp server")
	server := mcp.NewServer(&mcp.Implementation{Name: "CybertwinDataProxyService", Version: "0.1.0"}, nil)

	// Register tools
	tools.AddToolsToServer(server)

	serverConfig := config.GetServerConfig()
	
	// Use command line address if provided
	serverAddress := serverConfig.Address
	if address != "" {
		serverAddress = address
	}

	// Start server with appropriate transport
	if serverAddress != "" {
		authHandlerMiddleware := auth.RequireBearerToken(verifier.Verify, &auth.RequireBearerTokenOptions{
			Scopes: []string{"read"},
		})

		handler := mcp.NewStreamableHTTPHandler(func(*http.Request) *mcp.Server {
			return server
		}, nil)
		logger.Log.Infof("MCP server listening at %s", serverAddress)
		return http.ListenAndServe(serverAddress, authHandlerMiddleware(handler))
	} else {
		t := &mcp.LoggingTransport{Transport: &mcp.StdioTransport{}, Writer: os.Stderr}
		return server.Run(context.Background(), t)
	}
}
