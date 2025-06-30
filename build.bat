@echo off
setlocal

REM --- Konfigurasi Proyek ---
REM Pastikan MinGW-w64 (dengan gcc) ada di PATH Anda.
SET CC=gcc

SET SRC_DIR=src
SET LIB_DIR=lib
SET INCLUDE_DIR=include
SET TARGET=main.exe

REM --- Path Raylib & Raygui ---
SET RAYLIB_PATH=%LIB_DIR%\raylib
SET RAYGUI_PATH=%LIB_DIR%\raygui
SET RAYLIB_SRC_PATH=%RAYLIB_PATH%\src

REM --- File Sumber --- 
REM Gabungkan file sumber aplikasi Anda dan file sumber raylib yang diperlukan
SET APP_SOURCES=^
 %SRC_DIR%\main.c ^
 %SRC_DIR%\function\adlink_adc_dumy.c ^
 %SRC_DIR%\ui\wave_display.c ^
 %SRC_DIR%\ui\ppi_display.c ^
 %SRC_DIR%\ui\ppi_speed_slider.c ^
 %SRC_DIR%\ui\wave_controls.c ^
 %SRC_DIR%\ui\datetime_display.c ^
 %SRC_DIR%\ui\freq_analyzer.c

REM File sumber inti Raylib untuk platform desktop
SET RAYLIB_SOURCES=^
 %RAYLIB_SRC_PATH%\rcore.c ^
 %RAYLIB_SRC_PATH%\rglfw.c ^
 %RAYLIB_SRC_PATH%\rshapes.c ^
 %RAYLIB_SRC_PATH%\rtextures.c ^
 %RAYLIB_SRC_PATH%\rtext.c ^
 %RAYLIB_SRC_PATH%\rmodels.c ^
 %RAYLIB_SRC_PATH%\raudio.c ^
 %RAYLIB_SRC_PATH%\utils.c

REM --- Flags --- 
SET INCLUDE_FLAGS=^
 -I%INCLUDE_DIR% ^
 -I%RAYLIB_SRC_PATH% ^
 -I%RAYGUI_PATH% ^
 -I%RAYGUI_PATH%\src ^
 -I%RAYLIB_SRC_PATH%\external\glfw\include

SET COMPILER_FLAGS=-Wall -std=c99 -DPLATFORM_DESKTOP

SET LINKER_FLAGS=-lopengl32 -lgdi32 -lwinmm -luser32 -static

REM --- Logika Build ---

REM 1. Periksa dependensi
where %CC% >nul 2>nul
if %errorlevel% neq 0 ( echo ERROR: '%CC%' tidak ditemukan. Pastikan MinGW-w64 ada di PATH Anda. & goto :eof )

REM 2. Kompilasi dan Link dalam satu langkah
echo --- Mengkompilasi dan Menautkan Proyek ---
%CC% %APP_SOURCES% %RAYLIB_SOURCES% %INCLUDE_FLAGS% %COMPILER_FLAGS% -o %TARGET% %LINKER_FLAGS%

if "%errorlevel%" == "0" (
    echo.
    echo --- Build Berhasil ---
    echo Executable '%TARGET%' telah dibuat.
) else (
    echo.
    echo --- Build Gagal ---
)

endlocal
