Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "C:\Users\user\Desktop\出席管理アプリ.lnk"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "py.exe"
oLink.Arguments = "-m src.attendance_app"
oLink.WorkingDirectory = "C:\Users\user\attendance-management-system\attendance-management-system.3.2"
oLink.Save