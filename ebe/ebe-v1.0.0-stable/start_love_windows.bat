@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo EBE v1.0.0 - LÖVE2D launcher
echo.

if exist "%~dp0love-runtime\love.exe" if exist "%~dp0love-runtime\lua51.dll" (
  pushd "%~dp0love-runtime"
  love.exe "%~dp0"
  set ERR=%errorlevel%
  popd
  exit /b %ERR%
)

if exist "C:\Program Files\LOVE\love.exe" if exist "C:\Program Files\LOVE\lua51.dll" (
  pushd "C:\Program Files\LOVE"
  love.exe "%~dp0"
  set ERR=%errorlevel%
  popd
  exit /b %ERR%
)

if exist "C:\Program Files (x86)\LOVE\love.exe" if exist "C:\Program Files (x86)\LOVE\lua51.dll" (
  pushd "C:\Program Files (x86)\LOVE"
  love.exe "%~dp0"
  set ERR=%errorlevel%
  popd
  exit /b %ERR%
)

for /f "delims=" %%L in ('where love.exe 2^>nul') do (
  set "LOVEEXE=%%~fL"
  set "LOVEDIR=%%~dpL"
  if exist "!LOVEDIR!lua51.dll" (
    pushd "!LOVEDIR!"
    love.exe "%~dp0"
    set ERR=!errorlevel!
    popd
    exit /b !ERR!
  )
)

echo No complete LÖVE2D runtime found.
echo Keep love.exe, lua51.dll and the other LÖVE DLL files together.
echo You may place the complete runtime in:
echo   "%~dp0love-runtime\"
pause
exit /b 2
