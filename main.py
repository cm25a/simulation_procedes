from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI()

# Définition du modèle de données d'entrée (ce que l'utilisateur va envoyer)
class ParametresSimulation(BaseModel):
    m0: float           # Débit initial (kg/h)
    x0: float           # Fraction insoluble initiale
    y0: float           # Fraction soluble initiale
    mR: float           # Apport de jus concentré (kg/h)
    cR: float           # Concentration de l'apport
    cp: float           # Capacité calorifique (kJ/kg.K)
    T1: float           # Température initiale (°C)
    T2: float           # Température de chauffage (°C)
    T3: float           # Température finale de refroidissement (°C)
    y_final: float      # Concentration finale voulue
    lambda_vap: float   # Chaleur latente (kJ/kg)

@app.get("/", response_class=HTMLResponse)
async def lire_index(request: Request):
    # Lecture directe du fichier HTML sans Jinja2
    with open("index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.post("/simuler")
async def simuler(params: ParametresSimulation):
    # --- 1. FILTRATION ---
    m1 = params.m0 - (params.m0 * params.x0)
    y1 = (params.y0 * params.m0) / m1
    residus = params.m0 * params.x0

    # --- 2. MÉLANGE ---
    m_melange = m1 + params.mR
    y_melange = ((y1 * m1) + (params.cR * params.mR)) / m_melange

    # --- 3. CHAUFFAGE ---
    Q3 = m_melange * params.cp * (params.T2 - params.T1) / 3600

    # --- 4. ÉVAPORATION ---
    M_soluble = m_melange * y_melange
    m2 = M_soluble / params.y_final
    mvp = m_melange - m2
    Q4 = mvp * params.lambda_vap / 3600

    # --- 5. REFROIDISSEMENT ---
    Q5 = m2 * params.cp * (params.T2 - params.T3) / 3600

    # --- 6. BILAN GLOBAL ---
    entrees = params.m0 + params.mR
    sorties = residus + mvp + m2
    erreur = entrees - sorties

    # Retourne les résultats au format JSON
    return {
        "filtration": {"m1": round(m1, 2), "y1": round(y1, 4), "residus": round(residus, 2)},
        "melange": {"m_melange": round(m_melange, 2), "y_melange": round(y_melange, 4)},
        "chauffage": {"Q3": round(Q3, 2)},
        "evaporation": {"mvp": round(mvp, 2), "m2": round(m2, 2), "Q4": round(Q4, 2)},
        "refroidissement": {"Q5": round(Q5, 2)},
        "bilan": {"entrees": round(entrees, 2), "sorties": round(sorties, 2), "erreur": round(erreur, 6)}
    }