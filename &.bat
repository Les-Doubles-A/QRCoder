pip install customtkinter pillow qrcode pyinstaller
# placez QRCoder.png dans le dossier QRCoder/
python convert_icon.py
pyinstaller --noconsole --onefile --icon=QRCoder.ico --name=QRCoder main.py