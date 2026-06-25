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
	"net/http"
	"time"

	"github.com/ccnn-pcl/ccnn/AI_Twin/cybertwin/data_proxy/logger"
	"github.com/golang-jwt/jwt/v5"
	"github.com/modelcontextprotocol/go-sdk/auth"
)

// JWTClaims represents the claims in our JWT tokens.
type JWTClaims struct {
	UserID string   `json:"user_id"` // User identifier
	Scopes []string `json:"scopes"`  // Permissions/roles for the user
	jwt.RegisteredClaims
}

func Verify(ctx context.Context, tokenString string, _ *http.Request) (*auth.TokenInfo, error) {
	logger.Log.Infof("get token %v", tokenString)
	return &auth.TokenInfo{
		Scopes:     []string{"read"},                          // User permissions
		Expiration: time.Now().Add(10 * 365 * 24 * time.Hour), // Token expiration time
	}, nil
	/*
	   // Parse and validate the JWT token.

	   	token, err := jwt.ParseWithClaims(tokenString, &JWTClaims{}, func(token *jwt.Token) (any, error) {
	   		// Verify the signing method is HMAC.
	   		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
	   			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
	   		}
	   		return []byte("your-secret-key"), nil
	   	})

	   	if err != nil {
	   		// Return standard error for invalid tokens.
	   		return nil, fmt.Errorf("%w: %v", auth.ErrInvalidToken, err)
	   	}

	   // Extract claims and verify token validity.

	   	if claims, ok := token.Claims.(*JWTClaims); ok && token.Valid {
	   		return &auth.TokenInfo{
	   			Scopes:     claims.Scopes,         // User permissions
	   			Expiration: claims.ExpiresAt.Time, // Token expiration time
	   		}, nil
	   	}

	   return nil, fmt.Errorf("%w: invalid token claims", auth.ErrInvalidToken)
	*/
}
