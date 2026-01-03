from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import date, timedelta
import random

app = FastAPI(title="Flumen API", version="0.1.0")

# CORS (para que el frontend pueda llamar desde el navegador)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://flumen-frontend.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/health")
def health():
    return {"status": "ok", "service": "flumen-backend"}

# -------------------------
# DEMO DATA (en memoria)
# -------------------------
FUELS = ["VPOWER", "SUPER", "REGULAR", "DIESEL"]
PUMPS = [1, 2, 3, 4, 5, 6]

def make_open_day(d: date):
    """Genera un día ABIERTO con números coherentes (simulados)."""
    # Totales por combustible
    fuel_amounts = {
        "VPOWER": random.randint(18000, 35000),
        "SUPER": random.randint(35000, 55000),
        "REGULAR": random.randint(30000, 50000),
        "DIESEL": random.randint(10000, 20000),
    }
    total_sold = sum(fuel_amounts.values())

    vouchers = random.randint(8000, 25000)
    transfers = random.randint(5000, 20000)
    cash_expected = max(total_sold - vouchers - transfers, 0)

    # Desglose por bomba (distribución simple)
    pump_breakdown = []
    for p in PUMPS:
        row = {"pump": p}
        # repartimos cada combustible en 6 bombas con variación
        row_amounts = {}
        for f in FUELS:
            base = fuel_amounts[f] // 6
            jitter = random.randint(-800, 800)
            row_amounts[f] = max(base + jitter, 0)
        row["fuels"] = row_amounts
        row["total"] = sum(row_amounts.values())
        pump_breakdown.append(row)

    # Ajuste final para que el total por bombas cuadre aproximado (demo)
    return {
        "date": d.isoformat(),
        "status": "OPEN",
        "total_sold": total_sold,
        "vouchers": vouchers,
        "transfers": transfers,
        "cash_expected": cash_expected,
        "fuel_breakdown": fuel_amounts,
        "pump_breakdown": pump_breakdown,
    }

# Estado DEMO
DEMO = {
    "station": {"id": 1, "name": "Demo Central"},
    "history": [],
    "open_day": None,
}

def seed_if_needed():
    if DEMO["open_day"] is None:
        today = date.today()
        yesterday = today - timedelta(days=1)

        # Ayer cerrado (histórico)
        d0 = make_open_day(yesterday)
        d0["status"] = "CLOSED"
        DEMO["history"].append(d0)

        # Hoy abierto
        DEMO["open_day"] = make_open_day(today)

@app.get("/demo/dashboard")
def demo_dashboard():
    seed_if_needed()
    return {
        "station": DEMO["station"],
        "open_day": DEMO["open_day"],
        "history": DEMO["history"],  # lista de días cerrados
    }

@app.post("/demo/cutoff")
def demo_cutoff():
    seed_if_needed()

    if DEMO["open_day"]["status"] == "CLOSED":
        return {"ok": False, "message": "El día ya fue cerrado."}

    # Cierra el día y lo manda a histórico
    closed = dict(DEMO["open_day"])
    closed["status"] = "CLOSED"
    DEMO["history"].append(closed)

    # Crea nuevo día abierto (simula "día siguiente")
    new_date = date.fromisoformat(closed["date"]) + timedelta(days=1)
    DEMO["open_day"] = make_open_day(new_date)

    return {"ok": True, "message": "Corte realizado", "closed_date": closed["date"]}
