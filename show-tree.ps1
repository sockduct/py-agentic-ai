<#
.SYNOPSIS
Displays a directory tree using Linux tree-style formatting.

.DESCRIPTION
Shows the contents of a directory recursively with Unicode branch characters,
directory names ending in '/', and a final directory/file count summary.
Directories are displayed before files, with each group sorted by name. Hidden
items are included by default, while common repository noise directories are
excluded unless a different exclusion list is provided.

The script can be run directly from PowerShell, for example:

    .\show-tree.ps1

It also defines a Show-Tree function when dot-sourced.

.PARAMETER Path
The directory path to display. Defaults to the current directory.

.PARAMETER Exclude
One or more item names to omit from the output. Defaults to .git, .venv,
.ruff_cache, and .pytest_cache.

.PARAMETER Prefix
Internal indentation text used while rendering nested entries. This parameter
is retained for compatibility with earlier versions of the function and should
normally be left unset.

.EXAMPLE
.\show-tree.ps1

Displays the current directory as a tree.

.EXAMPLE
.\show-tree.ps1 -Path .\src

Displays the src directory as a tree.

.EXAMPLE
.\show-tree.ps1 -Exclude .git, .venv, node_modules

Displays the current directory while excluding the specified item names.

.EXAMPLE
. .\show-tree.ps1
Show-Tree -Path .

Dot-sources the script to make the Show-Tree function available, then displays
the current directory.
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$Path = ".",
    [string[]]$Exclude,
    [string]$Prefix = ""
)

$script:DefaultTreeExcludes = @(
    ".git", ".venv", ".ruff_cache", ".pytest_cache", ".mypy_cache", "__pycache__"
)

if (-not $PSBoundParameters.ContainsKey("Exclude")) {
    $Exclude = $script:DefaultTreeExcludes
    $PSBoundParameters["Exclude"] = $Exclude
}

function Show-Tree {
    [CmdletBinding()]
    param(
        [Parameter(Position = 0)]
        [string]$Path = ".",
        [string[]]$Exclude = $script:DefaultTreeExcludes,
        [string]$Prefix = ""
    )

    function Format-TreeRoot {
        param(
            [string]$RootPath,
            [System.IO.FileSystemInfo]$RootItem
        )

        if ($RootPath -eq "." -or $RootPath -eq ".\") {
            return "./"
        }

        if ($RootItem.PSIsContainer -and -not $RootPath.EndsWith("/") -and -not $RootPath.EndsWith("\")) {
            return "$RootPath/"
        }

        return $RootPath
    }

    function Write-TreeItems {
        param(
            [string]$CurrentPath,
            [string[]]$ExcludedNames,
            [string]$CurrentPrefix,
            [ref]$DirectoryCount,
            [ref]$FileCount
        )

        $items = @(Get-ChildItem -LiteralPath $CurrentPath -Force |
            Where-Object { $ExcludedNames -notcontains $_.Name } |
            Sort-Object @{ Expression = { -not $_.PSIsContainer } }, Name)

        for ($i = 0; $i -lt $items.Count; $i++) {
            $item = $items[$i]
            $last = $i -eq ($items.Count - 1)
            $branch = if ($last) { "└── " } else { "├── " }
            $displayName = if ($item.PSIsContainer) { "$($item.Name)/" } else { $item.Name }

            "$CurrentPrefix$branch$displayName"

            if ($item.PSIsContainer) {
                $DirectoryCount.Value++
                $nextPrefix = if ($last) { "$CurrentPrefix    " } else { "$CurrentPrefix│   " }
                Write-TreeItems -CurrentPath $item.FullName -ExcludedNames $ExcludedNames -CurrentPrefix $nextPrefix -DirectoryCount $DirectoryCount -FileCount $FileCount
            }
            else {
                $FileCount.Value++
            }
        }
    }

    $rootItem = Get-Item -LiteralPath $Path -Force
    $directoryCount = if ($rootItem.PSIsContainer) { 1 } else { 0 }
    $fileCount = if ($rootItem.PSIsContainer) { 0 } else { 1 }

    if ($Prefix -eq "") {
        Format-TreeRoot -RootPath $Path -RootItem $rootItem
    }

    if ($rootItem.PSIsContainer) {
        Write-TreeItems -CurrentPath $rootItem.FullName -ExcludedNames $Exclude -CurrentPrefix $Prefix -DirectoryCount ([ref]$directoryCount) -FileCount ([ref]$fileCount)
    }

    if ($Prefix -eq "") {
        $directoryLabel = if ($directoryCount -eq 1) { "directory" } else { "directories" }
        $fileLabel = if ($fileCount -eq 1) { "file" } else { "files" }

        ""
        "$directoryCount $directoryLabel, $fileCount $fileLabel"
    }
}

if ($MyInvocation.InvocationName -ne ".") {
    Show-Tree @PSBoundParameters
}
