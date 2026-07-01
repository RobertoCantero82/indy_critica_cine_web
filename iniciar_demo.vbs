' iniciar_demo.vbs — arranca backend y frontend en segundo plano, sin ventanas, y abre el navegador

Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' calculo la carpeta donde vive este script para no depender de dónde se lance desde
strDir = objFSO.GetParentFolderName(WScript.ScriptFullName)

' arranco el backend oculto, sin abrir ninguna ventana de consola
objShell.CurrentDirectory = strDir
objShell.Run "cmd /c python -m uvicorn backend.main:app --port 8000", 0, False

' arranco el frontend oculto desde su propia carpeta
objShell.Run "cmd /c cd /d """ & strDir & "\frontend"" && npm run dev", 0, False

' espero a que el frontend esté listo antes de abrir el navegador
WScript.Sleep 4000

' abro el navegador por defecto en la web ya arrancada
objShell.Run "http://localhost:5173", 1, False
