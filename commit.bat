@ECHO Off

REM the below line clears thread status so that i don't inadvertently upload wrong file. This is a comment btw

SET /p commit_msg="Commit message: "
git add .
IF "%commit_msg%"=="" (git commit -m "whateva") ELSE (git commit -m "%commit_msg%")
PAUSE