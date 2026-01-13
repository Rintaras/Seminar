@echo off
REM 完全自動ベンチマーク＆グラフ生成スクリプト (Windows用)
REM WSL (Windows Subsystem for Linux) が必要です

echo =========================================
echo 🚀 完全自動テスト開始 (Windows)
echo =========================================
echo.

REM 現在のディレクトリを取得
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM WSLの確認
where wsl >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ エラー: WSL (Windows Subsystem for Linux) が見つかりません
    echo.
    echo このスクリプトを実行するには、以下のいずれかが必要です:
    echo   1. WSL をインストールして、このスクリプトをWSL内で実行
    echo   2. Git Bash をインストールして、auto_benchmark.sh を実行
    echo   3. Docker Desktop をインストールして、以下を手動で実行:
    echo      - docker-compose down -v
    echo      - docker-compose build
    echo      - docker-compose up -d
    echo      - docker exec benchmark-client /app/scripts/run-experiments.sh
    echo.
    echo 推奨: Git Bash をインストールして以下を実行:
    echo   bash auto_benchmark.sh
    echo.
    pause
    exit /b 1
)

echo ℹ️ WSLを使用してスクリプトを実行します...
echo.

REM Windowsパスを取得してWSLパスに変換
for /f "usebackq tokens=*" %%i in (`wsl wslpath -a "%SCRIPT_DIR%"`) do set WSL_PATH=%%i

echo WSLパス: %WSL_PATH%
echo.

REM WSL内でBashスクリプトを実行
wsl bash "%WSL_PATH%auto_benchmark.sh"

if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ エラーが発生しました
    pause
    exit /b 1
)

echo.
echo =========================================
echo 🎉 処理完了！
echo =========================================
echo.
pause

