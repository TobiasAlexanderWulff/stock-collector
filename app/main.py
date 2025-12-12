from fastapi import FastAPI
from app.db import Base, engine
import app.models  # noqa: F401

app = FastAPI()

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
