<#
.SYNOPSIS
  Sets up Holographic Studio on a fresh Windows machine with a brand-new VS Code.

.DESCRIPTION
  Needs nothing but Windows PowerShell. Steps (each is skipped if already done):
    1. Python 3.13 (installed with winget for the current user if missing)
    2. desktop/.venv with every library from requirements-dev.txt
    3. the hand and body models (downloaded once into desktop/data/models)
    4. the Jupyter kernel "Holographic Studio (.venv)" for HolographicStudio.ipynb
    5. the VS Code extensions for Python and Jupyter (skip with -SkipExtensions)
    6. a quick check that everything imports and Panda3D can draw

  Run it by double-clicking setup.cmd, from a VS Code terminal with .\setup.cmd,
  or with Terminal > Run Task > "holostudio: cài đặt máy mới".

.PARAMETER SkipExtensions
  Do not install VS Code extensions.

.PARAMETER Run
  Start Holographic Studio when setup is done.
#>
param(
    [switch]$SkipExtensions,
    [switch]$Run
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$Root = $PSScriptRoot
$Venv = Join-Path $Root '.venv'
$VenvPython = Join-Path $Venv 'Scripts\python.exe'
$KernelName = 'holostudio'
$KernelLabel = 'Holographic Studio (.venv)'
$Extensions = @('ms-python.python', 'ms-toolsai.jupyter')

function Write-Step([string]$Text) { Write-Host "`n==> $Text" -ForegroundColor Cyan }
function Write-Ok([string]$Text) { Write-Host "    OK  $Text" -ForegroundColor Green }

function Invoke-Checked([string]$File, [string[]]$Arguments) {
    & $File @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Lệnh thất bại ($LASTEXITCODE): $File $($Arguments -join ' ')" }
}

function Test-Python313([string]$Candidate) {
    if (-not $Candidate) { return $false }
    try {
        $version = & $Candidate -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
        return ($LASTEXITCODE -eq 0 -and "$version".Trim() -eq '3.13')
    } catch { return $false }
}

function Find-Python313 {
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\python.exe'),
        (Join-Path $env:ProgramFiles 'Python313\python.exe')
    )
    $launcher = Get-Command py -ErrorAction SilentlyContinue
    if ($launcher) {
        try {
            $path = & $launcher.Source -3.13 -c "import sys; print(sys.executable)" 2>$null
            if ($LASTEXITCODE -eq 0) { $candidates = @("$path".Trim()) + $candidates }
        } catch { }
    }
    $onPath = Get-Command python -ErrorAction SilentlyContinue
    if ($onPath -and $onPath.Source -notlike '*WindowsApps*') { $candidates += $onPath.Source }
    foreach ($candidate in $candidates) {
        if ((Test-Path $candidate) -and (Test-Python313 $candidate)) { return $candidate }
    }
    return $null
}

function Find-CodeCli {
    $onPath = Get-Command code -ErrorAction SilentlyContinue
    if ($onPath) { return $onPath.Source }
    foreach ($candidate in @(
        (Join-Path $env:LOCALAPPDATA 'Programs\Microsoft VS Code\bin\code.cmd'),
        (Join-Path $env:ProgramFiles 'Microsoft VS Code\bin\code.cmd')
    )) {
        if (Test-Path $candidate) { return $candidate }
    }
    return $null
}

Push-Location $Root
try {
    # 1. Python ---------------------------------------------------------------
    Write-Step 'Python 3.13'
    $Python = Find-Python313
    if (-not $Python) {
        $winget = Get-Command winget -ErrorAction SilentlyContinue
        if (-not $winget) {
            throw 'Chưa có Python 3.13 và máy không có winget. Hãy cài Python 3.13 từ https://www.python.org/downloads/ rồi chạy lại setup.'
        }
        Write-Host '    Chưa có Python 3.13: đang cài bằng winget (cho người dùng hiện tại)…'
        Invoke-Checked $winget.Source @(
            'install', '--exact', '--id', 'Python.Python.3.13', '--scope', 'user',
            '--silent', '--accept-package-agreements', '--accept-source-agreements'
        )
        $Python = Find-Python313
        if (-not $Python) { throw 'Đã cài Python nhưng không tìm thấy python.exe. Hãy mở lại VS Code rồi chạy lại setup.' }
    }
    Write-Ok $Python

    # 2. Virtual environment and libraries -------------------------------------
    Write-Step 'Môi trường .venv và thư viện'
    if (-not (Test-Python313 $VenvPython)) {
        if (Test-Path $Venv) { Remove-Item -Recurse -Force $Venv }
        Invoke-Checked $Python @('-m', 'venv', $Venv)
    }
    Invoke-Checked $VenvPython @('-m', 'pip', 'install', '--quiet', '--upgrade', 'pip')
    Invoke-Checked $VenvPython @('-m', 'pip', 'install', '--quiet', '-r', 'requirements-dev.txt')
    Write-Ok $VenvPython

    # 3. Models ------------------------------------------------------------------
    Write-Step 'Model nhận diện tay và cơ thể (tải một lần)'
    # A module, not inline code: Windows PowerShell drops double quotes in native arguments.
    Invoke-Checked $VenvPython @('-m', 'holostudio.prepare')

    # 4. Jupyter kernel -----------------------------------------------------------
    Write-Step "Kernel Jupyter '$KernelLabel'"
    Invoke-Checked $VenvPython @('-m', 'ipykernel', 'install', '--user', '--name', $KernelName, '--display-name', $KernelLabel)
    Write-Ok "Chọn kernel '$KernelLabel' khi mở HolographicStudio.ipynb"

    # 5. VS Code extensions -----------------------------------------------------
    if ($SkipExtensions) {
        Write-Step 'Bỏ qua cài extension VS Code (-SkipExtensions)'
    } else {
        Write-Step 'Extension VS Code: Python + Jupyter'
        $code = Find-CodeCli
        if (-not $code) {
            Write-Host '    Không tìm thấy lệnh "code". Hãy cài thủ công trong VS Code: Python (ms-python.python) và Jupyter (ms-toolsai.jupyter).' -ForegroundColor Yellow
        } else {
            foreach ($extension in $Extensions) { Invoke-Checked $code @('--install-extension', $extension, '--force') }
            Write-Ok ($Extensions -join ', ')
        }
    }

    # 6. Check --------------------------------------------------------------------
    Write-Step 'Kiểm tra môi trường'
    Invoke-Checked $VenvPython @('-m', 'pytest', '-q', '-p', 'no:cacheprovider', 'tests/test_environment.py')
    Write-Ok 'Thư viện và Panda3D hoạt động'

    Write-Host "`nXong. Mở desktop/HolographicStudio.ipynb và chọn kernel '$KernelLabel', hoặc nhấn F5 trong VS Code." -ForegroundColor Green
    if ($Run) { Invoke-Checked $VenvPython @('run.py') }
}
finally {
    Pop-Location
}
