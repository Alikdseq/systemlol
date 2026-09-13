#Requires -Version 5.1
# Keeps Cloudflare quick tunnel alive for Mini App.
# On new URL: updates .env MINIAPP_URL, Telegram menu button, recreates bot container.
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $Root ".env"))) {
  $Root = $PSScriptRoot
}
$EnvFile = Join-Path $Root ".env"
$Cloudflared = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
if (-not (Test-Path $Cloudflared)) {
  $cmd = Get-Command cloudflared -ErrorAction SilentlyContinue
  if ($cmd) { $Cloudflared = $cmd.Source }
}
if (-not $Cloudflared -or -not (Test-Path $Cloudflared)) {
  Write-Error "cloudflared not found"
  exit 1
}

$Target = "http://localhost:8080"
$UrlRegex = [regex]'https://[a-zA-Z0-9-]+\.trycloudflare\.com'
$script:CurrentMiniappUrl = ""

function Read-DotEnv {
  param([string]$Path)
  $map = @{}
  if (-not (Test-Path $Path)) { return $map }
  Get-Content $Path -Encoding UTF8 | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith("#")) { return }
    $i = $line.IndexOf("=")
    if ($i -lt 1) { return }
    $map[$line.Substring(0, $i).Trim()] = $line.Substring($i + 1).Trim()
  }
  return $map
}

function Set-MiniappUrlInEnv {
  param([string]$Path, [string]$MiniappUrl)
  $lines = @()
  if (Test-Path $Path) {
    $lines = @(Get-Content $Path -Encoding UTF8)
  }
  $found = $false
  $out = foreach ($line in $lines) {
    if ($line -match '^\s*MINIAPP_URL\s*=') {
      $found = $true
      "MINIAPP_URL=$MiniappUrl"
    } else {
      $line
    }
  }
  if (-not $found) {
    $out = @($out) + @("MINIAPP_URL=$MiniappUrl")
  }
  Set-Content -Path $Path -Value $out -Encoding UTF8
}

function Update-TelegramMenu {
  param([string]$Token, [string]$MiniappUrl)
  if (-not $Token) { return $false }
  $payload = @{
    menu_button = @{
      type = "web_app"
      text = "Q Premium"
      web_app = @{ url = $MiniappUrl }
    }
  } | ConvertTo-Json -Depth 6 -Compress
  try {
    $resp = Invoke-RestMethod -Method Post `
      -Uri "https://api.telegram.org/bot$Token/setChatMenuButton" `
      -ContentType "application/json; charset=utf-8" `
      -Body ([System.Text.Encoding]::UTF8.GetBytes($payload)) `
      -TimeoutSec 20
    return [bool]$resp.ok
  } catch {
    Write-Warning ("Telegram setChatMenuButton failed: " + $_.Exception.Message)
    return $false
  }
}

function Restart-BotContainer {
  Push-Location $Root
  try {
    & docker compose up -d --force-recreate --no-deps bot | Out-Host
  } catch {
    Write-Warning ("docker compose bot recreate failed: " + $_.Exception.Message)
  } finally {
    Pop-Location
  }
}

function Apply-NewTunnelUrl {
  param([string]$BaseUrl)
  $mini = ($BaseUrl.TrimEnd("/") + "/app/")
  if ($script:CurrentMiniappUrl -eq $mini) { return }

  Write-Host ""
  Write-Host ("[tunnel] NEW URL -> " + $mini) -ForegroundColor Green
  Set-MiniappUrlInEnv -Path $EnvFile -MiniappUrl $mini
  $script:CurrentMiniappUrl = $mini
  $token = (Read-DotEnv $EnvFile)["TELEGRAM_BOT_TOKEN"]
  $ok = Update-TelegramMenu -Token $token -MiniappUrl $mini
  if ($ok) {
    Write-Host "[tunnel] Telegram menu: ok"
  } else {
    Write-Host "[tunnel] Telegram menu: fail"
  }
  Restart-BotContainer
  Write-Host "[tunnel] .env + bot updated. Open /start in Telegram."
  Write-Host ""
}

Write-Host "=== Q Premium tunnel keeper ===" -ForegroundColor Cyan
Write-Host ("Root:   " + $Root)
Write-Host ("Target: " + $Target)
Write-Host "Keep this window open. On tunnel drop: auto-restart + rewrite MINIAPP_URL in .env"
Write-Host ""

Get-Process cloudflared -ErrorAction SilentlyContinue | ForEach-Object {
  try { Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue } catch {}
}

$envMap = Read-DotEnv $EnvFile
if ($envMap["MINIAPP_URL"]) {
  $script:CurrentMiniappUrl = $envMap["MINIAPP_URL"]
}

while ($true) {
  $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  Write-Host ("[tunnel] starting cloudflared " + $stamp)
  try {
    & $Cloudflared tunnel --url $Target --no-autoupdate 2>&1 | ForEach-Object {
      $line = "$_"
      $m = $UrlRegex.Match($line)
      if ($m.Success) {
        Apply-NewTunnelUrl -BaseUrl $m.Value
      }
    }
  } catch {
    Write-Warning ("[tunnel] " + $_.Exception.Message)
  }
  Write-Warning "[tunnel] process exited. Restart in 5s..."
  Start-Sleep -Seconds 5
}
