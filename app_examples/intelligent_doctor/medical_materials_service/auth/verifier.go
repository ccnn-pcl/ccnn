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

package auth

import (
	"context"
	"fmt"
	"net/http"

	"github.com/ccnn-pcl/ccnn/app_examples/intelligent_doctor/medical_materials_service/logger"
	"github.com/golang-jwt/jwt/v5"
	"github.com/modelcontextprotocol/go-sdk/auth"
)

// JWTClaims represents the claims in our JWT tokens.
type JWTClaims struct {
	UserID     string   `json:"user_id"` // User identifier
	Scopes     []string `json:"scopes"`  // Permissions/roles for the user
	Department string   `json:"department"`
	DataTypes  string   `json:"data_types"`
	jwt.RegisteredClaims
}

func Verify(ctx context.Context, tokenString string, _ *http.Request) (*auth.TokenInfo, error) {
	// Parse and validate the JWT token.
	token, _, err := jwt.NewParser().ParseUnverified(tokenString, &JWTClaims{})
	if err != nil {
		// Return standard error for invalid tokens.
		return nil, fmt.Errorf("%w: %v", auth.ErrInvalidToken, err)
	}

	if err := verifySignature(ctx, tokenString); err != nil {
		logger.Log.Errorf("verify token error %v", err)
		return nil, err
	}
	token.Valid = true

	// Extract claims and verify token validity.
	if claims, ok := token.Claims.(*JWTClaims); ok && token.Valid {
		claims.Scopes = append(claims.Scopes, "read")
		return &auth.TokenInfo{
			Scopes:     claims.Scopes,         // User permissions
			Expiration: claims.ExpiresAt.Time, // Token expiration time
			Extra: map[string]any{
				"user_id":    claims.UserID,
				"department": claims.Department,
				"data_types": claims.DataTypes,
			},
		}, nil
	}

	return nil, fmt.Errorf("%w: invalid token claims", auth.ErrInvalidToken)
}
