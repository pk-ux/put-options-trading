@echo off
echo Pushing to GitHub...

cd /d "d:\Lenovo Ideapad D drive\VS code projects\options-trading"

REM Add the repository to safe.directory to avoid ownership issues
git config --global --add safe.directory "D:/Lenovo Ideapad D drive/VS code projects/options-trading"
echo Added repository to safe.directory

REM Set Git identity
git config --global user.email "flyingb5000@hotmail.com"
git config --global user.name "flyingb5000"
echo Git identity configured

REM Initialize Git repository if not already initialized
if not exist .git (
  git init
  echo Git repository initialized
)

REM Create .gitignore file if it doesn't exist
if not exist .gitignore (
  echo __pycache__/ > .gitignore
  echo *.py[cod] >> .gitignore
  echo *$py.class >> .gitignore
  echo .pytest_cache/ >> .gitignore
  echo build/ >> .gitignore
  echo dist/ >> .gitignore
  echo *.spec >> .gitignore
  echo .env >> .gitignore
  echo .venv >> .gitignore
  echo env/ >> .gitignore
  echo venv/ >> .gitignore
  echo ENV/ >> .gitignore
  echo config.json >> .gitignore
  echo .idea/ >> .gitignore
  echo .vscode/ >> .gitignore
  echo "Created .gitignore file"
)

REM Add all files
git add .
echo Files added to staging area

REM Commit changes
git commit -m "Initial commit of Options Trading Screener"
echo Changes committed

REM Set the remote repository URL to your GitHub repo
git remote add origin https://github.com/flyingb5000/options-trading.git || git remote set-url origin https://github.com/flyingb5000/options-trading.git
echo Remote repository set to: https://github.com/flyingb5000/options-trading.git

REM Push to GitHub using master branch (default for new repositories)
git push -u origin main
echo Code pushed to GitHub

pause