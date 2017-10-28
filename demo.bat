@echo off
cd market\webapp
start cmd /c "ng build --watch --base-href gui"
cd ..\..
set PYTHONPATH=.

echo Creating working directories..
mkdir State1 State2 State3 State4 State5

echo Creating bootstrap files..
set TRACKER=127.0.0.1 7001
echo %TRACKER% > State1\bootstraptribler.txt
echo %TRACKER% > State2\bootstraptribler.txt
echo %TRACKER% > State3\bootstraptribler.txt
echo %TRACKER% > State4\bootstraptribler.txt
echo %TRACKER% > State5\bootstraptribler.txt

echo Starting market communities..
start cmd /c "python market\main.py --dispersy 7001 --api 8001 --state State1 --bank --keypair keys\ABN-Amro.pem"
start cmd /c "python market\main.py --dispersy 7002 --api 8002 --state State2 --bank --keypair keys\Rabobank.pem"
start cmd /c "python market\main.py --dispersy 7003 --api 8003 --state State3 --borrower"
start cmd /c "python market\main.py --dispersy 7004 --api 8004 --state State4 --investor"
start cmd /k "python market\main.py --dispersy 7005 --api 8005 --state State5 --investor"
