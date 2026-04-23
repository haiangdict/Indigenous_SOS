@echo off
chcp 65001 > nul
echo ========================================
echo   App Update Script
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] Copying HTML files to www\...
copy /Y index.html www\index.html
copy /Y vocab.html www\vocab.html
copy /Y about.html www\about.html
echo Done.

echo [2/3] Copying data files to www\data\...
if not exist www\data mkdir www\data
copy /Y data\*.csv www\data\
copy /Y data\*.json www\data\
echo Done.

echo [3/3] Syncing to Android...
call npx cap sync android
echo Done.

echo.
echo ========================================
echo   Finished. Now rebuild APK in Android Studio:
echo   Build - Build APK(s) - Build APK(s)
echo ========================================
echo.
pause
