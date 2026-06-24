@echo off
chcp 65001 >nul
echo ============================================================
echo 医疗智能体项目启动器
echo ============================================================
echo.

echo 检查Python环境...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python未安装或未添加到PATH
    echo 请先安装Python 3.8+
    pause
    exit /b 1
)

echo.
echo 检查依赖...
python -c "import streamlit, sqlite3, asyncio" 2>nul
if %errorlevel% neq 0 (
    echo ❌ 缺少依赖，正在安装...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
)

echo.
echo 检查智能体模块...
python -c "from agents.coordinator import CybertwinAgent" 2>nul
if %errorlevel% neq 0 (
    echo ❌ 智能体模块导入失败
    echo 请检查agents目录是否存在
    pause
    exit /b 1
)

echo.
echo 创建必要目录...
if not exist "data" mkdir data
if not exist "data\backups" mkdir data\backups
if not exist "data\logs" mkdir data\logs

echo.
echo 运行快速测试...
python quick_test.py
if %errorlevel% neq 0 (
    echo ⚠️ 快速测试失败，但继续启动...
)

echo.
echo ============================================================
echo 启动Streamlit应用...
echo 访问地址: http://localhost:8501
echo 按 Ctrl+C 停止应用
echo ============================================================
echo.

set PYTHONPATH=%CD%
python -m streamlit run app.py

pause
