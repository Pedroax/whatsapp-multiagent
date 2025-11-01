# Fix broken API_URL patterns in frontend

$componentsPath = "c:\Users\Desktop\OneDrive\Área de Trabalho\alice-lc\frontend-multiagente\src\components"
$files = Get-ChildItem -Path $componentsPath -Filter *.tsx -Recurse

Write-Host "Fixing API URLs in $($files.Count) files..."

foreach ($file in $files) {
    Write-Host "Processing: $($file.Name)"
    $content = Get-Content $file.FullName -Raw

    # Fix pattern: "${API_URL}" -> 'http://138.68.13.174'
    $content = $content -replace '\$\{import\.meta\.env\.VITE_API_URL \|\| "\$\{API_URL\}"\}', '${import.meta.env.VITE_API_URL || ''http://138.68.13.174''}'

    # Fix single quote pattern: '${import.meta.env.VITE_API_URL || "${API_URL}"}' -> `${...}`
    $content = $content -replace '\'\$\{import\.meta\.env\.VITE_API_URL \|\| "\$\{API_URL\}"\}', '`${import.meta.env.VITE_API_URL || ''http://138.68.13.174''}'

    Set-Content $file.FullName -Value $content -NoNewline
}

Write-Host "`nDone! Fixed $($files.Count) files."
