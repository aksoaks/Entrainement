@echo off
:: Script de mise à jour Git automatisé avec gestion d'erreurs

set commit_msg="Last update: %date% %time%"

git add .
if %errorlevel% neq 0 (
    echo Échec de l'ajout des fichiers
    pause
    exit /b
)

git commit -m %commit_msg%
if %errorlevel% neq 0 (
    echo Échec du commit
    pause
    exit /b
)


git push origin main
if %errorlevel% neq 0 (
    echo Échec du push
    pause
    exit /b
)

echo Git Update Done !