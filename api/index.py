from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import os

app = FastAPI()

# Enable CORS for all origins, methods, and headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

TELEMETRY_FILE = "q-vercel-latency.json"

def load_telemetry():
    if os.path.exists(TELEMETRY_FILE):
        return pd.read_json(TELEMETRY_FILE)
    return pd.DataFrame()

@app.post("/")
async def analyze_telemetry(request: Request):
    body = await request.json()
    requested_regions = body.get("regions", [])
    threshold_ms = body.get("threshold_ms", 180)
    
    df = load_telemetry()
    results = {}
    
    if not df.empty and "region" in df.columns:
        for region in requested_regions:
            region_df = df[df["region"] == region]
            if region_df.empty:
                results[region] = {
                    "avg_latency": 0.0,
                    "p95_latency": 0.0,
                    "avg_uptime": 0.0,
                    "breaches": 0
                }
            else:
                latencies = region_df["latency_ms"]
                uptimes = region_df["uptime_pct"]
                
                avg_latency = float(latencies.mean())
                p95_latency = float(np.percentile(latencies, 95))
                avg_uptime = float(uptimes.mean())
                breaches = int((latencies > threshold_ms).sum())
                
                results[region] = {
                    "avg_latency": round(avg_latency, 2),
                    "p95_latency": round(p95_latency, 2),
                    "avg_uptime": round(avg_uptime, 2),
                    "breaches": breaches
                }
                
    return results