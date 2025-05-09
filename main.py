from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import csv
from io import StringIO

app = FastAPI()

# Permitir frontend do Vercel acessar
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ou especifique: ["https://iqvc-react.vercel.app"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        return {"error": "Arquivo deve ser CSV"}

    contents = await file.read()
    decoded = contents.decode('utf-8')
    csv_reader = csv.reader(StringIO(decoded))
    rows = list(csv_reader)

    return {
        "filename": file.filename,
        "rows_count": len(rows),
        "preview": rows[:3]  # só pra testar
    }
