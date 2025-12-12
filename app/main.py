from fastapi import FastAPI
from app.db import Base, engine

app = FastAPI()

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

