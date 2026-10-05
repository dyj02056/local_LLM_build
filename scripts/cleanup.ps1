# 프로젝트가 끝난 뒤 용량이 큰 파일을 정리한다.
#
#   .\scripts\cleanup.ps1                        # 무엇을 지울지 크기와 함께 보여 주기만 함 (기본)
#   .\scripts\cleanup.ps1 -Apply                 # 기본 대상(docker, ollama, data, deps)을 실제로 삭제
#   .\scripts\cleanup.ps1 -Only docker -Apply    # 특정 대상만 삭제
#   .\scripts\cleanup.ps1 -IncludeModels -Apply  # 파인튜닝 GGUF(models/*.gguf)까지 삭제 (복구하려면 Colab 재학습 또는 Drive)
#
# 지우지 않는 것: Git으로 관리되는 코드, models/ 의 Modelfile, 이 프로젝트와 무관한 Ollama 모델.

param(
    [switch]$Apply,
    [switch]$IncludeModels,
    [ValidateSet("docker", "ollama", "data", "deps", "models")]
    [string[]]$Only
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

# 이 프로젝트가 PC의 Ollama에 등록한 모델만
$OllamaModels = @("text2sql-ft", "text2sql-ft-v2", "qwen2.5-coder:3b")
$Folders = @{
    # outputs/(평가 결과)는 다시 만들려면 몇 시간이 걸려서 지우지 않는다
    data = @("data\spider", "data\sft", "data\korean\database", "data\korean\dev_ko.jsonl", "data\korean\dev_ext.jsonl", "data\korean_train")
    deps = @(".venv", "web\node_modules", "web\dist")
}

$targets = if ($Only) { $Only } else { @("docker", "ollama", "data", "deps") + $(if ($IncludeModels) { "models" }) }

function Get-SizeGB($path) {
    if (-not (Test-Path $path)) { return 0 }
    $item = Get-Item $path -Force
    if (-not $item.PSIsContainer) { return $item.Length / 1GB }
    return ((Get-ChildItem $path -Recurse -Force -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum) / 1GB
}

function Remove-Paths($paths) {
    foreach ($p in $paths) {
        if (Test-Path $p) {
            "  {0,7:N2} GB  {1}" -f (Get-SizeGB $p), $p
            if ($Apply) { Remove-Item $p -Recurse -Force -Confirm:$false }
        }
    }
}

$mode = if ($Apply) { "삭제합니다" } else { "미리보기 (지우려면 -Apply)" }
"=== 정리 대상: $($targets -join ', ') · $mode ==="

if ($targets -contains "docker") {
    "`n[docker] 컨테이너, 이미지, 모델 볼륨, 빌드 캐시"
    docker system df 2>$null
    if ($Apply) {
        docker compose down -v --rmi all
        docker builder prune -af | Out-Null
        "  Docker 안에서 지웠습니다. 실제 디스크를 돌려받으려면 Docker Desktop의 Clean / Purge data를 실행하세요."
    }
}

if ($targets -contains "ollama") {
    "`n[ollama] PC의 Ollama에서 이 프로젝트 모델만 삭제"
    $installed = (ollama list 2>$null) -join "`n"
    foreach ($m in $OllamaModels) {
        $name = if ($m.Contains(":")) { $m } else { "$m`:latest" }
        if ($installed -match "(?m)^$([regex]::Escape($name))\s") {
            "  $m"
            if ($Apply) { ollama rm $m | Out-Null }
        }
    }
}

if ($targets -contains "data") { "`n[data] 내려받거나 스크립트로 다시 만들 수 있는 데이터"; Remove-Paths $Folders.data }
if ($targets -contains "deps") { "`n[deps] 다시 설치할 수 있는 패키지"; Remove-Paths $Folders.deps }

if ($targets -contains "models") {
    "`n[models] 파인튜닝 GGUF (주의: 복구하려면 Drive에서 받거나 Colab 재학습)"
    Remove-Paths (Get-ChildItem models -Recurse -Filter *.gguf -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })
} elseif (-not $Only) {
    "`n[models] 보관 (지우려면 -IncludeModels)"
}

if (-not $Apply) { "`n미리보기만 했습니다. 실제로 지우려면 같은 명령에 -Apply 를 붙이세요." }
