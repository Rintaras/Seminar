@echo off
REM 環境チェックスクリプト (Windows用)
REM このスクリプトは問題診断のために使用します

echo =========================================
echo 🔍 環境チェック
echo =========================================
echo.

echo [1/5] 現在のディレクトリ
echo ----------------------------------------
echo %CD%
echo.

echo [2/5] スクリプトの場所
echo ----------------------------------------
echo %~dp0
echo.

echo [3/5] vol.2ディレクトリの内容
echo ----------------------------------------
if exist "%~dp0" (
    dir /b "%~dp0"
) else (
    echo ❌ vol.2ディレクトリが見つかりません
)
echo.

echo [4/5] resultsディレクトリの確認
echo ----------------------------------------
if exist "%~dp0results\" (
    echo ✅ resultsディレクトリが存在します
    echo.
    echo セッションディレクトリ:
    dir /b "%~dp0results\session_*" 2>nul
    if errorlevel 1 (
        echo ❌ セッションディレクトリが見つかりません
        echo    まず auto_benchmark.bat を実行してください
    )
) else (
    echo ❌ resultsディレクトリが見つかりません
    echo.
    echo 次のいずれかを実行してください:
    echo   1. auto_benchmark.bat - フルベンチマーク
    echo   2. auto_benchmark_5mbps.sh - 5Mbpsベンチマーク
)
echo.

echo [5/5] Dockerの確認
echo ----------------------------------------
where docker >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Docker がインストールされています
    echo.
    docker --version
    echo.
    echo Docker コンテナの状態:
    docker ps --filter "name=http" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
) else (
    echo ❌ Docker が見つかりません
    echo.
    echo Dockerをインストールしてください:
    echo https://www.docker.com/products/docker-desktop
)
echo.

echo [6/6] WSLの確認
echo ----------------------------------------
where wsl >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ WSL がインストールされています
    echo.
    wsl --list --verbose
) else (
    echo ❌ WSL が見つかりません
    echo.
    echo WSLをインストールすることを推奨します:
    echo   wsl --install
)
echo.

echo =========================================
echo ℹ️  推奨される実行方法
echo =========================================
echo.
echo ベンチマーク実行:
echo   方法1 ^(推奨^): cd vol.2 ^&^& bash auto_benchmark.sh
echo   方法2: cd vol.2 ^&^& auto_benchmark.bat
echo.
echo 結果確認:
echo   方法1 ^(推奨^): cd vol.2 ^&^& powershell -ExecutionPolicy Bypass -File view_results.ps1
echo   方法2: cd vol.2 ^&^& view_results.bat
echo   方法3: エクスプローラーで vol.2\results\ を開く
echo.

echo =========================================
echo 🔧 トラブルシューティング
echo =========================================
echo.
echo 問題: ウィンドウがすぐ閉じる
echo 解決: コマンドプロンプトから実行してください
echo   1. Win+R を押す
echo   2. 'cmd' と入力してEnter
echo   3. cd /d "%~dp0" と入力
echo   4. check_setup.bat と入力
echo.
echo 問題: Docker関連のエラー
echo 解決: Docker Desktop を起動してください
echo.
echo 問題: パス関連のエラー
echo 解決: vol.2 ディレクトリで実行していることを確認
echo.

pause

