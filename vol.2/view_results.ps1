# ベンチマーク結果確認スクリプト (PowerShell版)
# 使用方法: PowerShell で右クリック → "Run with PowerShell"
# または: powershell -ExecutionPolicy Bypass -File view_results.ps1

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "📊 ベンチマーク結果確認" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# 最新のセッションを探す
$sessions = Get-ChildItem -Path "results" -Directory -Filter "session_*" -ErrorAction SilentlyContinue | 
            Sort-Object LastWriteTime -Descending

if ($sessions.Count -eq 0) {
    Write-Host "❌ エラー: 結果ディレクトリが見つかりません" -ForegroundColor Red
    Write-Host ""
    Write-Host "まず、auto_benchmark.bat を実行してください。" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Enterキーを押して終了"
    exit 1
}

$latestSession = $sessions[0]
$sessionPath = $latestSession.FullName

Write-Host "✅ 最新セッション: " -NoNewline -ForegroundColor Green
Write-Host $latestSession.Name
Write-Host ""

# ファイル数を確認
$fileCount = (Get-ChildItem -Path $sessionPath -File -Recurse).Count

Write-Host "📁 セッションパス:" -ForegroundColor White
Write-Host "   $sessionPath" -ForegroundColor Gray
Write-Host ""
Write-Host "📊 生成されたファイル数: " -NoNewline -ForegroundColor White
Write-Host $fileCount -ForegroundColor Yellow
Write-Host ""

# セッション情報を表示
$sessionInfoPath = Join-Path $sessionPath "session_info.txt"
if (Test-Path $sessionInfoPath) {
    Write-Host "========== セッション情報 ==========" -ForegroundColor Cyan
    Get-Content $sessionInfoPath | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
    Write-Host "===================================" -ForegroundColor Cyan
    Write-Host ""
}

# 実験ディレクトリをリスト
Write-Host "📂 実験ディレクトリ:" -ForegroundColor White
Get-ChildItem -Path $sessionPath -Directory -Filter "delay_*" | ForEach-Object {
    $fileCount = (Get-ChildItem -Path $_.FullName -File).Count
    Write-Host "   - $($_.Name) " -NoNewline -ForegroundColor Yellow
    Write-Host "($fileCount ファイル)" -ForegroundColor Gray
}
Write-Host ""

# 分析ファイルをリスト
$analysisPath = Join-Path $sessionPath "analysis"
if (Test-Path $analysisPath) {
    Write-Host "📈 分析ファイル:" -ForegroundColor White
    Get-ChildItem -Path $analysisPath -File | ForEach-Object {
        $size = "{0:N2} KB" -f ($_.Length / 1KB)
        Write-Host "   - $($_.Name) " -NoNewline -ForegroundColor Yellow
        Write-Host "($size)" -ForegroundColor Gray
    }
    Write-Host ""
}

# レポートプレビュー
$reportPath = Join-Path $analysisPath "summary_report.txt"
if (Test-Path $reportPath) {
    Write-Host "========== レポートプレビュー ==========" -ForegroundColor Cyan
    Get-Content $reportPath | Select-Object -First 30 | ForEach-Object { 
        Write-Host $_ -ForegroundColor Gray 
    }
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

# オプションメニュー
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "オプション:" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "1. Explorerで結果フォルダを開く"
Write-Host "2. すべてのグラフを表示"
Write-Host "3. 詳細レポートを表示"
Write-Host "4. CSVファイルをExcelで開く"
Write-Host "5. 終了"
Write-Host ""

$choice = Read-Host "選択してください (1-5)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "📁 Explorerで開いています..." -ForegroundColor Green
        Start-Process explorer.exe -ArgumentList $sessionPath
    }
    "2" {
        Write-Host ""
        Write-Host "📊 グラフを表示しています..." -ForegroundColor Green
        Get-ChildItem -Path $analysisPath -Filter "*.png" -ErrorAction SilentlyContinue | ForEach-Object {
            Start-Process $_.FullName
        }
    }
    "3" {
        Write-Host ""
        if (Test-Path $reportPath) {
            Get-Content $reportPath | Out-Host
        } else {
            Write-Host "❌ レポートファイルが見つかりません" -ForegroundColor Red
        }
    }
    "4" {
        Write-Host ""
        Write-Host "📄 CSVファイルを検索しています..." -ForegroundColor Green
        $csvFiles = Get-ChildItem -Path $sessionPath -Filter "*.csv" -Recurse
        if ($csvFiles.Count -gt 0) {
            Write-Host "見つかったCSVファイル: $($csvFiles.Count)" -ForegroundColor Yellow
            $csvFiles | ForEach-Object {
                Write-Host "   開いています: $($_.Name)" -ForegroundColor Gray
                Start-Process $_.FullName
            }
        } else {
            Write-Host "❌ CSVファイルが見つかりません" -ForegroundColor Red
        }
    }
    default {
        Write-Host ""
        Write-Host "👋 終了します" -ForegroundColor Yellow
    }
}

Write-Host ""
Read-Host "Enterキーを押して終了"



