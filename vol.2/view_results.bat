@echo off
REM ベンチマーク結果確認スクリプト (Windows用)

REM エラー発生時も続行してメッセージを表示
setlocal enabledelayedexpansion

echo =========================================
echo 📊 ベンチマーク結果確認
echo =========================================
echo.
echo デバッグ情報:
echo - 現在のディレクトリ: %CD%
echo - スクリプトの場所: %~dp0
echo.

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo スクリプトディレクトリに移動しました: %CD%
echo.

REM resultsディレクトリの存在確認
if not exist "results\" (
    echo ❌ エラー: resultsディレクトリが見つかりません
    echo.
    echo 現在のディレクトリ: %CD%
    echo.
    echo 以下を確認してください:
    echo   1. vol.2 ディレクトリにいるか確認
    echo   2. まず auto_benchmark.bat を実行してください
    echo.
    echo 手動で確認する場合:
    echo   cd /d "%~dp0"
    echo   dir results
    echo.
    pause
    exit /b 1
)

echo resultsディレクトリが見つかりました
echo.

REM 最新のセッションを探す
set LATEST_SESSION=
for /f "delims=" %%i in ('dir /b /ad /o-d results\session_* 2^>nul') do (
    if not defined LATEST_SESSION set LATEST_SESSION=%%i
)

if "%LATEST_SESSION%"=="" (
    echo ❌ エラー: セッションディレクトリが見つかりません
    echo.
    echo resultsディレクトリ内のフォルダ:
    dir /b results
    echo.
    echo まず、auto_benchmark.bat を実行してください。
    echo.
    pause
    exit /b 1
)

set SESSION_PATH=results\%LATEST_SESSION%

echo ✅ 最新セッション: %LATEST_SESSION%
echo.

REM ファイル数を確認
set FILE_COUNT=0
for /r "%SESSION_PATH%" %%f in (*.*) do set /a FILE_COUNT+=1

echo 📁 セッションパス:
echo    %SESSION_PATH%
echo.
echo 📊 生成されたファイル数: %FILE_COUNT%
echo.

REM セッション情報を表示
if exist "%SESSION_PATH%\session_info.txt" (
    echo ========== セッション情報 ==========
    type "%SESSION_PATH%\session_info.txt"
    echo ===================================
    echo.
)

REM 実験ディレクトリをリスト
echo 📂 実験ディレクトリ:
for /d %%d in ("%SESSION_PATH%\delay_*") do (
    echo    - %%~nxd
)
echo.

REM 分析ファイルをリスト
if exist "%SESSION_PATH%\analysis" (
    echo 📈 分析ファイル:
    for %%f in ("%SESSION_PATH%\analysis\*.*") do (
        echo    - %%~nxf (%%~zf bytes)
    )
    echo.
)

REM レポートプレビュー
if exist "%SESSION_PATH%\analysis\summary_report.txt" (
    echo ========== レポートプレビュー ==========
    powershell -Command "Get-Content '%SESSION_PATH%\analysis\summary_report.txt' | Select-Object -First 30"
    echo =======================================
    echo.
)

echo.
echo =========================================
echo オプション:
echo =========================================
echo 1. Finderで結果フォルダを開く
echo 2. グラフを表示
echo 3. 詳細レポートを表示
echo 4. 終了
echo.
set /p CHOICE="選択してください (1-4): "

if "%CHOICE%"=="1" (
    echo.
    echo 📁 Explorerで開いています...
    explorer "%SESSION_PATH%"
) else if "%CHOICE%"=="2" (
    echo.
    echo 📊 グラフを表示しています...
    if exist "%SESSION_PATH%\analysis\ttfb_comparison.png" start "" "%SESSION_PATH%\analysis\ttfb_comparison.png"
    if exist "%SESSION_PATH%\analysis\throughput_comparison.png" start "" "%SESSION_PATH%\analysis\throughput_comparison.png"
) else if "%CHOICE%"=="3" (
    echo.
    if exist "%SESSION_PATH%\analysis\summary_report.txt" (
        type "%SESSION_PATH%\analysis\summary_report.txt"
    ) else (
        echo ❌ レポートファイルが見つかりません
    )
) else (
    echo.
    echo 👋 終了します
)

echo.
pause

