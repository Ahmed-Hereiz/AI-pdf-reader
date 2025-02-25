#!/bin/bash

rm -rf build dist AI_pdf_reader_linux AI_pdf_reader_linux.zip
pyinstaller --onefile --windowed open_pdf.py

mkdir -p AI_pdf_reader_linux
cp dist/open_pdf AI_pdf_reader_linux/

# Copy additional project files (adjust if your structure is different)
cp call_ai.py AI_pdf_reader_linux/
cp -r customAgents* AI_pdf_reader_linux/
cp -r assets AI_pdf_reader_linux/
cp -r helpers AI_pdf_reader_linux/
cp -r RAG AI_pdf_reader_linux/

cat <<EOF > AI_pdf_reader_linux/AI_pdf_reader.desktop
[Desktop Entry]
Name=AI PDF Reader
Exec=/home/ahmed-hereiz/self/pdf-AI-reader/AI_pdf_reader_linux/open_pdf
Icon=/home/ahmed-hereiz/self/pdf-AI-reader/AI_pdf_reader_linux/assets/app_icon.png
Type=Application
Terminal=true
EOF

chmod +x AI_pdf_reader_linux/open_pdf
chmod +x AI_pdf_reader_linux/AI_pdf_reader.desktop
zip -r AI_pdf_reader_linux.zip AI_pdf_reader_linux

echo "Linux build complete: AI_pdf_reader_linux.zip created."
