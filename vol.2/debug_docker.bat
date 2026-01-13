@echo off
REM Docker環境デバッグスクリプト (Windows用)

echo =========================================
echo 🔍 Docker環境デバッグ
echo =========================================
echo.

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo [1/7] 現在のディレクトリ
echo ----------------------------------------
echo %CD%
echo.

echo [2/7] Dockerの状態確認
echo ----------------------------------------
docker --version 2>nul
if %errorlevel% neq 0 (
    echo ❌ Docker が見つかりません
    echo    Docker Desktop をインストールしてください
    echo    https://www.docker.com/products/docker-desktop
    goto :end
)
echo ✅ Docker が利用可能です
echo.

echo [3/7] Docker Desktop の起動確認
echo ----------------------------------------
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker daemon が起動していません
    echo    Docker Desktop を起動してください
    goto :end
)
echo ✅ Docker daemon が起動しています
echo.

echo [4/7] コンテナの状態
echo ----------------------------------------
docker ps --filter "name=http" --filter "name=benchmark" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo.

echo [5/7] resultsディレクトリの確認（ホスト側）
echo ----------------------------------------
if exist "results\" (
    echo ✅ resultsディレクトリが存在します
    echo.
    echo 内容:
    dir /b results 2>nul
    if errorlevel 1 (
        echo    （空）
    )
) else (
    echo ❌ resultsディレクトリが見つかりません
    echo    作成しています...
    mkdir results
)
echo.

echo [6/7] Docker内のファイルシステム確認
echo ----------------------------------------
docker ps --filter "name=benchmark-client" --format "{{.Names}}" | findstr benchmark-client >nul
if %errorlevel% equ 0 (
    echo ✅ benchmark-client コンテナが起動しています
    echo.
    echo Docker内の /app/results の内容:
    docker exec benchmark-client ls -la /app/results 2>nul
    echo.
    echo Docker内の /app ディレクトリの内容:
    docker exec benchmark-client ls -l /app 2>nul | findstr -i "http\|benchmark\|scripts"
) else (
    echo ❌ benchmark-client コンテナが起動していません
    echo.
    echo コンテナを起動してください:
    echo    docker-compose up -d
)
echo.

echo [7/7] ボリュームマウントの確認
echo ----------------------------------------
docker inspect benchmark-client 2>nul | findstr -i "source.*results" >nul
if %errorlevel% equ 0 (
    echo ✅ ボリュームマウントが設定されています
    echo.
    echo 詳細:
    docker inspect benchmark-client --format="{{range .Mounts}}{{.Type}}: {{.Source}} -> {{.Destination}}{{println}}{{end}}" 2>nul
) else (
    echo ⚠️  ボリュームマウント情報を取得できません
)
echo.

echo =========================================
echo 📊 診断結果
echo =========================================
echo.

REM 総合診断
set ISSUES=0

docker ps --filter "name=benchmark-client" --format "{{.Names}}" | findstr benchmark-client >nul
if %errorlevel% neq 0 (
    echo ❌ 問題: benchmark-client コンテナが起動していません
    echo    解決: docker-compose up -d
    set /a ISSUES+=1
)

if not exist "results\" (
    echo ❌ 問題: resultsディレクトリが存在しません
    echo    解決: mkdir results
    set /a ISSUES+=1
)

if %ISSUES% equ 0 (
    echo ✅ 重大な問題は見つかりませんでした
    echo.
    echo テストベンチマークを実行してみてください:
    echo    docker exec benchmark-client /app/scripts/run-benchmark.sh 10 https://172.20.0.10:2000/ https://172.20.0.11:3000/ 0 0 test
    echo.
    echo その後、resultsディレクトリを確認:
    echo    dir results\test
) else (
    echo.
    echo ⚠️  %ISSUES% 個の問題が見つかりました
    echo    上記の解決方法を試してください
)

echo.

:end
echo.
echo =========================================
echo 📝 推奨される次のステップ
echo =========================================
echo.
echo 1. 問題がある場合は修正してください
echo 2. ベンチマークを実行:
echo    方法A: bash auto_benchmark.sh
echo    方法B: auto_benchmark.bat
echo.
echo 3. 結果を確認:
echo    powershell -ExecutionPolicy Bypass -File view_results.ps1
echo.
echo 4. 問題が続く場合:
echo    - Docker Desktop を再起動
echo    - docker-compose down -v
echo    - docker-compose build --no-cache
echo    - docker-compose up -d
echo.

pause

