@echo off
:: Script de mise à jour Git automatisé avec gestion d'erreurs

set commit_msg="Last update: %date% %time%"

echo [1/3] Ajout des fichiers...
git add .
if %errorlevel% neq 0 (
    echo Échec de l'ajout des fichiers
    pause
    exit /b
)

echo [2/3] Commit avec message: %commit_msg%
git commit -m %commit_msg%
if %errorlevel% neq 0 (
    echo Échec du commit
    pause
    exit /b
)

echo [3/3] Push vers GitHub...
git push origin main
if %errorlevel% neq 0 (
    echo Échec du push
    pause
    exit /b
)

echo Mise à jour terminée avec succès!
timeout /t 3