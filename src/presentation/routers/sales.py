from application.use_cases.initiate_sale import InitiateSale
from application.use_cases.list_sold_vehicles import ListSoldVehicles
from fastapi import APIRouter, Depends, HTTPException, Query, status
from infrastructure.auth.oauth2 import get_current_user
from infrastructure.database.database import get_session
from infrastructure.database.sale_repository_impl import SaleRepositoryImpl
from infrastructure.http.catalog_client import (
    CatalogClient,
    CatalogUnavailableError,
    VehicleNotAvailableError,
    VehicleNotFoundError,
)
from presentation.schemas.sale_schemas import (
    SaleCreateRequest,
    SaleResponse,
    SoldListingResponse,
)

router = APIRouter(prefix="/sales", tags=["Sales"])


def _get_use_case(session=Depends(get_session)) -> InitiateSale:
    return InitiateSale(
        repository=SaleRepositoryImpl(session),
        catalog=CatalogClient(),
    )


@router.post("", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
async def initiate_sale(
    body: SaleCreateRequest,
    _: dict = Depends(get_current_user),
    use_case: InitiateSale = Depends(_get_use_case),
) -> SaleResponse:
    try:
        sale = await use_case.execute(
            vehicle_id=body.vehicle_id,
            buyer_cpf=body.buyer_cpf,
            sale_date=body.sale_date,
        )
    except VehicleNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Veículo não encontrado no catálogo.",
        ) from err
    except VehicleNotAvailableError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Veículo já foi vendido.",
        ) from err
    except CatalogUnavailableError as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de catálogo indisponível. Tente novamente.",
        ) from err

    return SaleResponse.model_validate(sale)


def _get_list_use_case(session=Depends(get_session)) -> ListSoldVehicles:
    return ListSoldVehicles(repository=SaleRepositoryImpl(session))


@router.get("/sold", response_model=SoldListingResponse, status_code=status.HTTP_200_OK)
async def list_sold_vehicles(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: dict = Depends(get_current_user),
    use_case: ListSoldVehicles = Depends(_get_list_use_case),
) -> SoldListingResponse:
    items, total = await use_case.execute(page=page, page_size=page_size)
    return SoldListingResponse(
        items=[SaleResponse.model_validate(s) for s in items],
        total=total,
        page=page,
        page_size=page_size,
    )
