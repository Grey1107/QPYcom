@echo off

rem 全局变量
rem originFile 是替换的文件， targetFile 是被替换掉的文件
set originFile=C:\Users\Delectate\Desktop\t1.txt
set targetFile=C:\Users\Delectate\Desktop\t2.txt

rem 等待 5 秒
echo wait one second
ping 1.1.1.1 -n 1 -w 5000 > nul

rem 杀死 wxglade_out.exe
:killProc
echo kill wxglade_out.exe
taskkill /F /IM wxglade_out.exe

rem	等待wxglade_out.exe结束再进行下一步
:proCheck
echo check wxglade_out.exe, waitting
ping 1.1.1.1 -n 1 -w 1000 > nul
tasklist | find "wxglade_out.exe" /i
if "%errorlevel%"=="0" goto :proCheck

rem 替换
echo replace wxglade_out.exe
move /y "%originFile%" "%targetFile%"

rem 等待 5 秒
echo wait one second
ping 1.1.1.1 -n 1 -w 5000 > nul

rem 运行 wxglade_out.exe
echo start wxglade_out.exe
start %CD%\wxglade_out.exe

rem 删除批处理自身
echo remove bat file
del /f /q %0