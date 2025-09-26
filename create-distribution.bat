@echo off
echo Creating NIC PDF Generator Distribution Package...
echo.

REM Create distribution folder
if exist "NIC_PDF_Generator_Distribution" rmdir /s /q "NIC_PDF_Generator_Distribution"
mkdir "NIC_PDF_Generator_Distribution"

REM Copy the Electron app
echo Copying Electron app...
xcopy "dist-electron\win-unpacked" "NIC_PDF_Generator_Distribution\app" /E /I /Q

REM Copy server and dependencies
echo Copying server files...
copy "server.js" "NIC_PDF_Generator_Distribution\"
copy "package.json" "NIC_PDF_Generator_Distribution\"

REM Copy Python scripts
echo Copying Python scripts...
copy "*.py" "NIC_PDF_Generator_Distribution\"

REM Copy assets
echo Copying assets...
xcopy "fonts" "NIC_PDF_Generator_Distribution\fonts" /E /I /Q
copy "*.jpg" "NIC_PDF_Generator_Distribution\" 2>nul
copy "*.jpeg" "NIC_PDF_Generator_Distribution\" 2>nul
copy "*.png" "NIC_PDF_Generator_Distribution\" 2>nul

REM Copy React build
echo Copying React app...
xcopy "dist" "NIC_PDF_Generator_Distribution\dist" /E /I /Q

REM Install Node.js dependencies properly
echo Installing Node.js dependencies...
cd "NIC_PDF_Generator_Distribution"
npm install
cd ..

REM Create launcher
echo Creating launcher...
echo @echo off > "NIC_PDF_Generator_Distribution\Start_NIC_PDF_Generator.bat"
echo echo Starting NIC PDF Generator... >> "NIC_PDF_Generator_Distribution\Start_NIC_PDF_Generator.bat"
echo echo. >> "NIC_PDF_Generator_Distribution\Start_NIC_PDF_Generator.bat"
echo. >> "NIC_PDF_Generator_Distribution\Start_NIC_PDF_Generator.bat"
echo REM Kill any existing processes >> "NIC_PDF_Generator_Distribution\Start_NIC_PDF_Generator.bat"
echo taskkill /f /im "NIC PDF Generator.exe" 2^>nul >> "NIC_PDF_Generator_Distribution\Start_NIC_PDF_Generator.bat"
echo taskkill /f /im "node.exe" 2^>nul >> "NIC_PDF_Generator_Distribution\Start_NIC_PDF_Generator.bat"
echo. >> "NIC_PDF_Generator_Distribution\Start_NIC_PDF_Generator.bat"
echo REM Wait a moment >> "NIC_PDF_Generator_Distribution\Start_NIC_PDF_Generator.bat"
echo timeout /t 2 /nobreak ^>nul >> "NIC_PDF_Generator_Distribution\Start_NIC_PDF_Generator.bat"
echo. >> "NIC_PDF_Generator_Distribution\Start_NIC_PDF_Generator.bat"
echo REM Start the server in background >> "NIC_PDF_Generator_Distribution\Start_NIC_PDF_Generator.bat"
echo echo Starting server... >> "NIC_PDF_Generator_Distribution\Start_NIC_PDF_Generator.bat"
echo start /b node server.js >> "NIC_PDF_Generator_Distribution\Start_NIC_PDF_Generator.bat"
echo. >> "NIC_PDF_Generator_Distribution\Start_NIC_PDF_Generator.bat"
echo REM Wait for server to start >> "NIC_PDF_Generator_Distribution\Start_NIC_PDF_Generator.bat"
echo timeout /t 3 /nobreak ^>nul >> "NIC_PDF_Generator_Distribution\Start_NIC_PDF_Generator.bat"
echo. >> "NIC_PDF_Generator_Distribution\Start_NIC_PDF_Generator.bat"
echo REM Start the Electron app >> "NIC_PDF_Generator_Distribution\Start_NIC_PDF_Generator.bat"
echo echo Starting desktop app... >> "NIC_PDF_Generator_Distribution\Start_NIC_PDF_Generator.bat"
echo if exist "app\NIC PDF Generator.exe" ^( >> "NIC_PDF_Generator_Distribution\Start_NIC_PDF_Generator.bat"
echo     start "" "app\NIC PDF Generator.exe" >> "NIC_PDF_Generator_Distribution\Start_NIC_PDF_Generator.bat"
echo ^) else ^( >> "NIC_PDF_Generator_Distribution\Start_NIC_PDF_Generator.bat"
echo     echo Error: NIC PDF Generator.exe not found! >> "NIC_PDF_Generator_Distribution\Start_NIC_PDF_Generator.bat"
echo     pause >> "NIC_PDF_Generator_Distribution\Start_NIC_PDF_Generator.bat"
echo ^) >> "NIC_PDF_Generator_Distribution\Start_NIC_PDF_Generator.bat"
echo. >> "NIC_PDF_Generator_Distribution\Start_NIC_PDF_Generator.bat"
echo echo. >> "NIC_PDF_Generator_Distribution\Start_NIC_PDF_Generator.bat"
echo echo App launched! You can close this window. >> "NIC_PDF_Generator_Distribution\Start_NIC_PDF_Generator.bat"

REM Create README for users
echo Creating user instructions...
echo NIC PDF Generator > "NIC_PDF_Generator_Distribution\README.txt"
echo =================== >> "NIC_PDF_Generator_Distribution\README.txt"
echo. >> "NIC_PDF_Generator_Distribution\README.txt"
echo INSTALLATION: >> "NIC_PDF_Generator_Distribution\README.txt"
echo 1. Copy this entire folder to your computer >> "NIC_PDF_Generator_Distribution\README.txt"
echo 2. Double-click "Start_NIC_PDF_Generator.bat" to run the application >> "NIC_PDF_Generator_Distribution\README.txt"
echo. >> "NIC_PDF_Generator_Distribution\README.txt"
echo REQUIREMENTS: >> "NIC_PDF_Generator_Distribution\README.txt"
echo - Windows 10 or later >> "NIC_PDF_Generator_Distribution\README.txt"
echo - No additional software installation required >> "NIC_PDF_Generator_Distribution\README.txt"
echo. >> "NIC_PDF_Generator_Distribution\README.txt"
echo USAGE: >> "NIC_PDF_Generator_Distribution\README.txt"
echo 1. Run "Start_NIC_PDF_Generator.bat" >> "NIC_PDF_Generator_Distribution\README.txt"
echo 2. The application window will open automatically >> "NIC_PDF_Generator_Distribution\README.txt"
echo 3. Upload your Excel file and generate PDFs >> "NIC_PDF_Generator_Distribution\README.txt"
echo. >> "NIC_PDF_Generator_Distribution\README.txt"
echo SUPPORT: >> "NIC_PDF_Generator_Distribution\README.txt"
echo Contact IT Support if you encounter any issues >> "NIC_PDF_Generator_Distribution\README.txt"

echo.
echo ✅ Distribution package created successfully!
echo 📁 Location: NIC_PDF_Generator_Distribution\
echo 🚀 Users can run: Start_NIC_PDF_Generator.bat
echo.
pause