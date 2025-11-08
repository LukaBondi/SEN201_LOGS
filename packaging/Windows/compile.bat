copy packaging\main.spec main.spec
pyinstaller --noconfirm main.spec
DEL /F main.spec
