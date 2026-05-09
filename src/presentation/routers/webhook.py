from fastapi import APIRouter, Depends, HTTPException, status

from application.use_cases.process_payment_callback import (
    ProcessPaymentCallback,
    SaleNotFoundError,
    SaleNotModifiableError,
)
from infrastructure.auth.oauth2 import make_service_token
from infrastructure.database.database import get_session
from infrastructure.database.sale_repository_impl import SaleRepositoryImpl
from infrastructure.http.catalog_client import CatalogClient
from presentation.schemas.webhook_schemas import (
    WebhookPaymentRequest,
    WebhookPaymentResponse,
)

router = APIRouter(prefix="/webhook", tags=["Webhook"])


def _get_use_case(session=Depends(get_session)) -> ProcessPaymentCallback:
    return ProcessPaymentCallback(
        repository=SaleRepositoryImpl(session),
        catalog=CatalogClient(token=make_service_token()),
    )


@router.post(
    "/payment", response_model=WebhookPaymentResponse, status_code=status.HTTP_200_OK
)
async def payment_callback(
    body: WebhookPaymentRequest,
    use_case: ProcessPaymentCallback = Depends(_get_use_case),
) -> WebhookPaymentResponse:
    try:
        sale = await use_case.execute(
            payment_code=body.payment_code,
            payment_status=body.status,
        )
    except SaleNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Código de pagamento não encontrado.",
        ) from err
    except SaleNotModifiableError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta venda não está pendente de pagamento.",
        ) from err

    return WebhookPaymentResponse(
        sale_id=sale.id,
        payment_code=sale.payment_code,
        status=sale.status,
        updated_at=sale.updated_at,
    )
