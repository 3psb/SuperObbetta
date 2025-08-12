# SuperObbetta

SuperObbetta è un semplice platform a scorrimento orizzontale in stile "Super Mario".
Protagonista: la tua immagine (sprite realistico). L'eroina può camminare, saltare e lanciare **rossetti** e **smalti** (munizioni illimitate).

## Requisiti
- Python 3.10+
- pip install pygame

## Esecuzione in sviluppo
```bash
pip install pygame
python main.py
```

## Compilare un EXE con PyInstaller (locale)
```bash
pip install pyinstaller
pyinstaller --onefile --add-data "assets;assets" main.py
# su PowerShell: --add-data "assets;assets"
# risultato in dist/main.exe
```

## Build automatico con GitHub Actions
Questo repository include un workflow che costruisce l'exe su Windows quando fai push sul branch `main` o esegui manualmente il workflow.

## Contenuto
- main.py (codice del gioco)
- assets/ (sprite creati automaticamente e suoni WAV)
- .github/workflows/build.yml (workflow per creare l'exe)
