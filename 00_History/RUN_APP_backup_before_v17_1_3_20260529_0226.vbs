Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c cd /d C:\SageMirror_Production && python -m streamlit run app_v17_1_2.py --server.port 8505 --theme.base=""dark""", 0, False
MsgBox "현자의 거울 실행 완료!" & Chr(13) & "브라우저: http://localhost:8505", 64, "Sage Mirror v17.1.2"
