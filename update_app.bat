@echo off
chcp 65001 > nul
echo ========================================
echo   Payrang族語自救會 App 更新腳本
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] 複製網頁檔案到 www\...
copy /Y index.html www\ > nul
copy /Y vocab.html www\ > nul
copy /Y about.html www\ > nul
echo       HTML 檔案完成

echo [2/3] 複製資料檔案到 www\data\...
if not exist www\data mkdir www\data
xcopy /E /Y /Q data\*.csv www\data\ > nul 2>&1
xcopy /E /Y /Q data\*.json www\data\ > nul 2>&1
echo       資料檔案完成

echo [3/3] 同步到 Android...
call npx cap sync android
echo       Android 同步完成

echo.
echo ========================================
echo   完成！請在 Android Studio 重新編譯 APK
echo   Build ^> Build APK(s) ^> Build APK(s)
echo ========================================
echo.
pause
