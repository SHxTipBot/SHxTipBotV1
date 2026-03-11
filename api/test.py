from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/api/test")
def test_route():
    return JSONResponse({"status": "Vercel Python build works!"})
