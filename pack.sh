pyinstaller --name AssFontManager --windowed main.py \
  --add-data "./venv/lib/python3.12/site-packages/tkinterdnd2:tkinterdnd2" \
  --clean --noconfirm

#pyinstaller main.spec