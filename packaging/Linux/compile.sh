cp packaging/main.spec main.spec
pyinstaller --noconfirm main.spec
rm -f main.spec
