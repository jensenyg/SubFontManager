# 编译配置 =======
param (
    [string]$Configuration = "Release",
    [string]$Platform = "x64",
    [string]$SolutionPath,
    [string]$ProjectName = "fontmatch",
    [string]$OutputDir
)

if (-not $SolutionPath) {
    $SolutionPath = Join-Path $PSScriptRoot "fontmatch.sln"
}

if (-not $OutputDir) {
    $OutputDir = Join-Path (Split-Path -Parent $PSScriptRoot) "\SubFontManager"
}


# 查找系统中安装的VS实例中的MSBuild.exe =======
$msbuildCmd = Get-Command msbuild -ErrorAction SilentlyContinue
if ($msbuildCmd) {  # 尝试全局变量是否可用
    $msbuild = $msbuildCmd.Path
}
else {  # 使用vswhere工具
    $vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
    if (-not (Test-Path $vswhere)) {
        Write-Error "vswhere.exe not found."
        exit 1
    }

    # 查找带有 MSBuild 的 VS 安装实例
    $installationPath = & $vswhere -latest -requires Microsoft.Component.MSBuild -property installationPath
    if (-not $installationPath) {
        Write-Error "No Visual Studio installation with MSBuild found."
        exit 1
    }

    # 拼接 MSBuild 路径（适用于 VS 2017+）
    $msbuild = Join-Path $installationPath "MSBuild\Current\Bin\MSBuild.exe"
    if (-not (Test-Path $msbuild)) {
        Write-Error "MSBuild.exe not found at expected path: $msbuild"
        exit 1
    }
}


# 开始编译 =======
Write-Host "==> Building solution: $SolutionPath"

if (-Not (Test-Path $msbuild)) {
    $msbuild = "msbuild" # fallback to PATH
}

# Build
& $msbuild $SolutionPath /t:Build "/p:Configuration=$Configuration;Platform=$Platform"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed."
    exit 1
}

# Find DLL
$dllPath = Join-Path $PSScriptRoot "$Platform\$Configuration\$ProjectName.dll"
if (-Not (Test-Path $dllPath)) {
    Write-Host "DLL not found: $dllPath"
    exit 1
}

# Create output dir
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

# Copy
Copy-Item $dllPath "$OutputDir\" -Force

Write-Host "Build and copy complete. DLL at: $OutputDir\$ProjectName.dll"
