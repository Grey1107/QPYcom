@echo off

rem 全局变量
rem originFile 是替换的文件， targetFile 是被替换掉的文件
set programName=QPYcom.exe
set originFile=%~dp0temp\%programName%
set targetFile=%~dp0%programName%
set test=%~dp0


rem 杀死 QPYcom.exe
:killProc
echo kill QPYcom.exe
taskkill /F /IM QPYcom.exe

rem 等待 5 秒
choice /t 5 /d y /n >nul


del %targetFile%

rem 替换
echo replace QPYcom.exe
move /y "%originFile%" "%test%"

rem 等待 5 秒
choice /t 5 /d y /n >nul

rem 运行 QPYcom.exe
echo start QPYcom.exe
start %CD%\QPYcom.exe update

rem 删除批处理自身
echo remove bat file
del /f /q %0

