Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c cd /d C:\SageMirror_Production && python -m streamlit run app_v17_1_4A.py --server.port 8505 --theme.base=""dark""", 0, False
MsgBox "Sage Mirror Studio started." & Chr(13) & "Browser: http://localhost:8505", 64, "Sage Mirror v17.1.4-A"
