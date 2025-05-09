from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import csv
from io import StringIO
from collections import defaultdict
import re
import os
import pandas as pd
import tempfile

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def parse_score(cell):
    """Extrai número entre parênteses, mesmo com espaços: ( 8 ), (9), etc."""
    match = re.search(r"\(\s*(\d+)\s*\)", cell.strip())
    return int(match.group(1)) if match else None

@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        return {"error": "Arquivo deve ser CSV"}

    contents = await file.read()
    decoded = contents.decode('utf-8')
    reader = csv.reader(StringIO(decoded))
    rows = list(reader)

    headers = rows[0]
    data_rows = rows[1:]

    # Localizar colunas de Missão e Regional
    idx_missao = next(i for i, h in enumerate(headers) if "Missão" in h)
    idx_regional = next(i for i, h in enumerate(headers) if "Regional" in h)
    idx_inicio_perguntas = max(idx_missao, idx_regional) + 1
    perguntas = headers[idx_inicio_perguntas:]

    # Agrupar respostas válidas (com número entre parênteses)
    por_missao = defaultdict(lambda: defaultdict(list))
    por_regional = defaultdict(lambda: defaultdict(list))

    for row in data_rows:
        if len(row) < idx_inicio_perguntas:
            continue
        missao = row[idx_missao].strip()
        regional = row[idx_regional].strip()
        for i, cell in enumerate(row[idx_inicio_perguntas:]):
            pergunta = perguntas[i]
            nota = parse_score(cell)
            if nota is not None:
                por_missao[missao][pergunta].append(nota)
                por_regional[regional][pergunta].append(nota)

    # Calcular média
    def calcular_media(grupo):
        return {
            grupo_nome: {
                pergunta: round(sum(notas) / len(notas), 2)
                for pergunta, notas in perguntas_dict.items() if notas
            }
            for grupo_nome, perguntas_dict in grupo.items()
        }

    medias_missao = calcular_media(por_missao)
    medias_regional = calcular_media(por_regional)

    # Gerar CSVs temporários
    temp_dir = tempfile.gettempdir()
    missao_path = os.path.join("static", "medias_por_missao.csv")
    regional_path = os.path.join("static", "medias_por_regional.csv")
    pd.DataFrame(medias_missao).T.to_csv(missao_path, index=True)
    pd.DataFrame(medias_regional).T.to_csv(regional_path, index=True)

    return {
        "por_missao": medias_missao,
        "por_regional": medias_regional,
        "links": {
            "missao_csv": "/download/medias_por_missao.csv",
            "regional_csv": "/download/medias_por_regional.csv"
        }
    }

@app.get("/download/{filename}")
def download_csv(filename: str):
    file_path = os.path.join("static", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type='text/csv', filename=filename)
    return {"error": "Arquivo não encontrado"}