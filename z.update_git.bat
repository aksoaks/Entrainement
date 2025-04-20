@echo off
:: Script silencieux sauf erreurs et message final

set commit_msg="Last update: %date% %time%"

:: Ajouter tous les fichiers, cacher la sortie normale
git add . >nul
if %errorlevel% neq 0 (
    echo [ERREUR] Échec de l'ajout des fichiers
    pause
    exit /b
)

:: Commit avec message, cacher la sortie normale
git commit -m %commit_msg% >nul
if %errorlevel% neq 0 (
    echo [ERREUR] Échec du commit
    pause
    exit /b
)

:: Push vers la branche main, cacher la sortie normale
git push origin main >nul
if %errorlevel% neq 0 (
    echo [ERREUR] Échec du push
    pause
    exit /b
)

:: Message de confirmation
echo Git Update Done !
