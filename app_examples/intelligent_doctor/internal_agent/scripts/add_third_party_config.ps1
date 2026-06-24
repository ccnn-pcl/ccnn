# 添加第三方应用配置到 .env 文件
# ==========================================

$envFile = ".env"
$configFile = "config\env_example_third_party.txt"

Write-Host "检查 .env 文件..." -ForegroundColor Cyan

# 检查 .env 文件是否存在
if (-not (Test-Path $envFile)) {
    Write-Host ".env 文件不存在，从模板创建..." -ForegroundColor Yellow
    Copy-Item $configFile $envFile
    Write-Host ".env 文件已创建" -ForegroundColor Green
} else {
    Write-Host ".env 文件已存在" -ForegroundColor Green
    
    # 检查是否已包含第三方应用配置
    $content = Get-Content $envFile -Raw
    if ($content -match "THIRD_PARTY_MODE") {
        Write-Host "检测到已存在第三方应用配置" -ForegroundColor Yellow
        Write-Host "请手动检查配置是否正确：" -ForegroundColor Yellow
        Write-Host "  - THIRD_PARTY_MODE=real_api" -ForegroundColor Yellow
        Write-Host "  - DATA_PROXY_APP_URL=http://localhost:9000" -ForegroundColor Yellow
        Write-Host "  - DATABASE_STORAGE_BEIJING_URL=http://localhost:8001" -ForegroundColor Yellow
        Write-Host "  - DATABASE_STORAGE_SHANGHAI_URL=http://localhost:8001" -ForegroundColor Yellow
    } else {
        Write-Host "未检测到第三方应用配置，添加配置..." -ForegroundColor Yellow
        
        # 读取第三方应用配置
        $thirdPartyConfig = Get-Content $configFile | Where-Object {
            $_ -match "^THIRD_PARTY|^DATA_PROXY|^DATABASE_STORAGE" -and $_ -notmatch "^#"
        }
        
        # 追加到 .env 文件
        Add-Content -Path $envFile -Value "`n# ===================================================================================="
        Add-Content -Path $envFile -Value "# 第三方应用配置（自动添加）"
        Add-Content -Path $envFile -Value "# ===================================================================================="
        Add-Content -Path $envFile -Value $thirdPartyConfig
        
        Write-Host "第三方应用配置已添加到 .env 文件" -ForegroundColor Green
    }
}

Write-Host "`n配置完成！" -ForegroundColor Green
Write-Host "请检查 .env 文件，确保以下配置正确：" -ForegroundColor Cyan
Write-Host "  THIRD_PARTY_MODE=real_api" -ForegroundColor White
Write-Host "  DATA_PROXY_APP_URL=http://localhost:9000" -ForegroundColor White
Write-Host "  DATABASE_STORAGE_BEIJING_URL=http://localhost:8001" -ForegroundColor White
Write-Host "  DATABASE_STORAGE_SHANGHAI_URL=http://localhost:8001" -ForegroundColor White

