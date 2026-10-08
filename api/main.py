from fastapi import FastAPI, HTTPException
from api.data import SISMOS

app = FastAPI(title="Datos Sismos")


@app.get("/sismos")
def listar_sismos():
    return list(SISMOS.values())


@app.get("/sismos/{sismo_id}")
def obtener_sismo(sismo_id: str):
    sismo = SISMOS.get(sismo_id)
    if sismo is None:
        raise HTTPException(status_code=404, detail=f"Sismo {sismo_id} no encontrado")
    return sismo