@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
REM 完全自動ベンチマーク＆グラフ生成スクリプト (Windows用)

echo =========================================
echo 完全自動テスト開始 (Windows)
echo =========================================
echo.

REM 現在のディレクトリを取得
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Dockerの確認
docker --version >nul 2>&1
if %ERRORLEVEL% neq 0 goto :docker_error

docker-compose --version >nul 2>&1
if %ERRORLEVEL% neq 0 goto :docker_error

goto :docker_ok

:docker_error
echo [エラー] Docker または docker-compose が見つかりません
echo.
echo このスクリプトを実行するには、Docker Desktop が必要です:
echo   1. Docker Desktop をインストールしてください
echo   2. Docker Desktop を起動してください
echo   3. このスクリプトを再度実行してください
echo.
pause
exit /b 1

:docker_ok

echo [情報] Dockerを使用してスクリプトを実行します...
echo.

REM Step 1: Docker環境の準備
echo =========================================
echo Step 1: Docker環境の準備...
echo =========================================
echo.

echo Docker環境を再構築中...
docker-compose down -v
if %ERRORLEVEL% neq 0 (
    echo [警告] docker-compose down でエラーが発生しましたが、続行します...
)

REM 既存のネットワークを削除（重複エラーを防ぐため）
echo 既存のネットワークを削除中...
docker network rm vol2_benchmark-net 2>nul
docker network rm benchmark-net 2>nul
REM 未使用のネットワークを削除
docker network prune -f >nul 2>&1

docker-compose build
if %ERRORLEVEL% neq 0 (
    echo [エラー] docker-compose build に失敗しました
    pause
    exit /b 1
)

docker-compose up -d
if %ERRORLEVEL% neq 0 (
    echo [エラー] docker-compose up に失敗しました
    pause
    exit /b 1
)

echo サーバー起動待機中...
ping 127.0.0.1 -n 11 >nul

REM スクリプトファイルの改行コードを修正（CRLF -> LF）
echo スクリプトファイルの改行コードを修正中...
docker exec benchmark-client bash -c "find /app/scripts -name '*.sh' -exec sed -i 's/\r$//' {} \;"

echo.
echo コンテナ起動状態:
docker ps | findstr /i "http benchmark"

REM Step 2: ベンチマーク実行
echo.
echo =========================================
echo Step 2: ベンチマーク実行（3条件）
echo =========================================
echo.

REM セッションタイムスタンプを生成（YYYYMMDD_HHMMSS形式）
for /f "tokens=*" %%i in ('powershell -Command "Get-Date -Format 'yyyyMMdd_HHmmss'"') do set SESSION_TIMESTAMP=%%i
set SESSION_NAME=auto_test
set SESSION_DIR=/app/results/session_%SESSION_TIMESTAMP%_%SESSION_NAME%

echo セッション: %SESSION_DIR%
echo.

REM セッション情報ファイルを作成
docker exec benchmark-client bash -c "mkdir -p %SESSION_DIR% && echo 'Session Name: %SESSION_NAME%' > %SESSION_DIR%/session_info.txt && echo 'Start Time: '$(date '+%%Y-%%m-%%d %%H:%%M:%%S') >> %SESSION_DIR%/session_info.txt && echo 'Requests per condition: 30' >> %SESSION_DIR%/session_info.txt && echo 'Total conditions: 3' >> %SESSION_DIR%/session_info.txt"

REM 各条件でベンチマークを実行
echo Running experiment: delay_0ms_bw_unlimited (delay=0ms, bandwidth=unlimited)
docker exec benchmark-client bash -c "export PARENT_SESSION_DIR=%SESSION_DIR% && /app/scripts/run-benchmark.sh 30 https://172.20.0.10:2000/ https://172.20.0.11:3000/ 0 0 delay_0ms_bw_unlimited"
ping 127.0.0.1 -n 3 >nul

echo.
echo Running experiment: delay_50ms_bw_unlimited (delay=50ms, bandwidth=unlimited)
docker exec benchmark-client bash -c "export PARENT_SESSION_DIR=%SESSION_DIR% && /app/scripts/run-benchmark.sh 30 https://172.20.0.10:2000/ https://172.20.0.11:3000/ 50 0 delay_50ms_bw_unlimited"
ping 127.0.0.1 -n 3 >nul

echo.
echo Running experiment: delay_100ms_bw_unlimited (delay=100ms, bandwidth=0)
docker exec benchmark-client bash -c "export PARENT_SESSION_DIR=%SESSION_DIR% && /app/scripts/run-benchmark.sh 30 https://172.20.0.10:2000/ https://172.20.0.11:3000/ 100 0 delay_100ms_bw_unlimited"
ping 127.0.0.1 -n 3 >nul

REM セッション情報を更新
docker exec benchmark-client bash -c "echo 'End Time: '$(date '+%%Y-%%m-%%d %%H:%%M:%%S') >> %SESSION_DIR%/session_info.txt && echo 'Status: Completed' >> %SESSION_DIR%/session_info.txt"

echo.
echo =========================================
echo ベンチマーク完了
echo =========================================
echo.

REM Step 3: グラフ生成
echo =========================================
echo Step 3: グラフ生成（Docker内で実行）
echo =========================================
echo.

echo Docker内でグラフを生成中...
docker exec benchmark-client python3 /app/scripts/analyze_results.py %SESSION_DIR%
if %ERRORLEVEL% neq 0 (
    echo.
    echo [エラー] グラフ生成に失敗しました
    echo.
    echo トラブルシューティング:
    echo   1. Dockerコンテナが起動しているか確認:
    echo      docker ps ^| findstr benchmark-client
    echo.
    echo   2. セッションディレクトリが存在するか確認:
    echo      docker exec benchmark-client ls -la %SESSION_DIR%
    echo.
    echo   3. 手動でグラフを生成:
    echo      docker exec benchmark-client python3 /app/scripts/analyze_results.py %SESSION_DIR%
    echo.
    set HOST_SESSION_PATH=%SCRIPT_DIR%results\session_%SESSION_TIMESTAMP%_%SESSION_NAME%
    echo データは保存されています:
    echo   %HOST_SESSION_PATH%
    goto :end
)

echo.
echo =========================================
echo すべて完了！
echo =========================================
echo.

set HOST_SESSION_PATH=%SCRIPT_DIR%results\session_%SESSION_TIMESTAMP%_%SESSION_NAME%
echo 結果ディレクトリ（ホスト側）:
echo   %HOST_SESSION_PATH%
echo.

echo 生成されたファイル（Docker内）:
docker exec benchmark-client ls -lh %SESSION_DIR%/analysis/ 2>nul
echo.

REM サマリーレポートの確認
docker exec benchmark-client test -f %SESSION_DIR%/analysis/summary_report.txt >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo レポート:
    echo   %HOST_SESSION_PATH%\analysis\summary_report.txt
    echo.
    echo レポートプレビュー:
    echo ---
    docker exec benchmark-client head -30 %SESSION_DIR%/analysis/summary_report.txt
    echo ---
    echo.
) else (
    echo [警告] summary_report.txt が見つかりません
    echo.
)

echo 結果の確認方法:
echo   - ファイルエクスプローラーで以下を開く:
echo     %HOST_SESSION_PATH%\analysis\
echo.
echo   - またはコマンドで確認:
echo     explorer %HOST_SESSION_PATH%\analysis\
echo.

:end
echo =========================================
echo 処理完了！
echo =========================================
echo.
pause
