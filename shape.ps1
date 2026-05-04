# Run with

# .\shape.ps1 to get a list of all working files in the repository

# If downloaded in a zip, you may need to unblock the file before running:
# Unblock-File -Path .\shape.ps1

Clear-Host
$root = Get-Location
$excludeDirs = @(".git", ".lake", ".venv", ".cache", "__pycache__", ".pytest_cache", ".ruff_cache", "node_modules", "dist", "build", "site")

Get-ChildItem -File -Recurse |
Where-Object {
    $parts = $_.FullName -split '[\\/]'
    -not ($parts | Where-Object { $excludeDirs -contains $_ })
} |
ForEach-Object {
    Resolve-Path -Relative $_.FullName
}
