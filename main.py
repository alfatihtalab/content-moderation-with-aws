from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from routers import s3_router, text_moderation_router, media_moderation_router

app = FastAPI()




origins = ["*"]

app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,  # Allow cookies to be sent with cross-origin requests
        allow_methods=["*"],     # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
        allow_headers=["*"],     # Allow all headers
    )

app.include_router(s3_router)
app.include_router(text_moderation_router)
app.include_router(media_moderation_router)



@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

