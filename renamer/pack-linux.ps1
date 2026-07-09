param(
    [switch]$FrameworkDependent,
    [ValidateSet("linux-x64", "linux-arm64")]
    [string]$Runtime = "linux-x64"
)

$ErrorActionPreference = "Stop"
$project = Join-Path $PSScriptRoot "Renamer.csproj"
$outDir = Join-Path (Join-Path $PSScriptRoot "artifacts") "publish-$Runtime"

if ($FrameworkDependent) {
    dotnet publish $project -c Release -r $Runtime -o $outDir --self-contained false
}
else {
    dotnet publish $project -c Release -r $Runtime -o $outDir --self-contained true `
        -p:PublishSingleFile=true `
        -p:IncludeNativeLibrariesForSelfExtract=true
}

Write-Host ""
Write-Host "Output: $outDir"
Write-Host "Copy that folder to your Linux machine, then: chmod +x Renamer && ./Renamer [options]"
