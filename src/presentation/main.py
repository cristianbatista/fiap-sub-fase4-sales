from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from presentation.routers import sales, token, webhook

app = FastAPI(
    title="Sales Service",
    description="Vehicle sale flow — FIAP Vehicle Resale Platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(422)
async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    from fastapi.exceptions import RequestValidationError

    if isinstance(exc, RequestValidationError):
        errors = [
            {"campo": ".".join(str(loc) for loc in e["loc"]), "mensagem": e["msg"]}
            for e in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": errors},
        )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Dados inválidos."},
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erro interno do servidor."},
    )


app.include_router(token.router)
app.include_router(sales.router)
app.include_router(webhook.router)


@app.get("/health", tags=["Health"])
async def health() -> dict:
    return {"status": "ok"}
