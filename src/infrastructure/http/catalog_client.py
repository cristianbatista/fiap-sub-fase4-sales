import os

import httpx


class VehicleNotFoundError(Exception):
    def __init__(self, vehicle_id: str) -> None:
        self.vehicle_id = vehicle_id
        super().__init__(f"Vehicle {vehicle_id} not found in catalog")


class VehicleNotAvailableError(Exception):
    def __init__(self, vehicle_id: str) -> None:
        self.vehicle_id = vehicle_id
        super().__init__(f"Vehicle {vehicle_id} is not available")


class CatalogUnavailableError(Exception):
    pass


class CatalogClient:
    def __init__(self, token: str | None = None) -> None:
        base_url = os.environ["CATALOG_SERVICE_URL"]
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        self._client = httpx.AsyncClient(
            base_url=base_url, timeout=5.0, headers=headers
        )

    async def get_vehicle(self, vehicle_id: str) -> dict:
        try:
            response = await self._client.get(f"/vehicles/{vehicle_id}")
        except httpx.RequestError as err:
            raise CatalogUnavailableError("Catalog service unreachable") from err

        if response.status_code == 404:
            raise VehicleNotFoundError(vehicle_id)
        if response.status_code != 200:
            raise CatalogUnavailableError(
                f"Catalog returned unexpected status {response.status_code}"
            )

        vehicle = response.json()
        if vehicle.get("status") != "available":
            raise VehicleNotAvailableError(vehicle_id)

        return vehicle

    async def update_vehicle_status(self, vehicle_id: str, status: str) -> None:
        for attempt in range(2):
            try:
                response = await self._client.patch(
                    f"/vehicles/{vehicle_id}/status",
                    json={"status": status},
                )
                if response.status_code < 500:
                    return
            except httpx.RequestError:
                if attempt == 1:
                    return
