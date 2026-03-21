@echo off
pushd "%ProgramFiles(x86)%"
for /f "delims=" %%i in ('dir gbak.exe /s /b 2^>nul') do set GBAK=%%i
popd
if not exist "%GBAK%" (
  pushd "%ProgramFiles%"
  for /f "delims=" %%i in ('dir gbak.exe /s /b 2^>nul') do set GBAK=%%i
popd )
if exist "%GBAK%" (
  choice /M "Do you want to convert the archive to be compatible with software version older than 9.0?"
  if errorlevel 2 goto :EXIT
  if not exist ZDBDIR2.IB.XE3 ( rename ZDBDIR2.IB ZDBDIR2.IB.XE3
  if errorlevel 1 goto EXIT )
  "%GBAK%" -r ZDBDIR2.IBk ZDBDIR2.IB -user sysdba -password masterkey
  if errorlevel 1 ( echo Restore failed. & rename ZDBDIR2.IB.XE3 ZDBDIR2.IB
  ) else ( echo Archive has been converted. )
) else ( echo gbak.exe not found. )
:EXIT
pause