"""
Client accounts management routes for LedgerPro Accountants.
"""

from typing import List
from fastapi import APIRouter, HTTPException, status
from app.schemas.client import ClientCreate, ClientResponse, ClientUpdate
from app.data.mock_db import db

router = APIRouter(prefix="/clients", tags=["Clients & Corporate Accounts"])


@router.get(
    "",
    response_model=List[ClientResponse],
    summary="List all accounting corporate clients",
    description="Retrieve all registered business clients, their billing currency, and current outstanding balances.",
)
def list_clients():
    return db.get_all_clients()


@router.get(
    "/{client_id}",
    response_model=ClientResponse,
    summary="Get single client profile",
    description="Retrieve full details for an accounting client by unique client ID.",
)
def get_client(client_id: str):
    client = db.get_client(client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with ID '{client_id}' does not exist in LedgerPro database.",
        )
    return client


@router.post(
    "",
    response_model=ClientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new corporate client",
    description="Onboard a new client into LedgerPro accounting system. Requires company name, valid tax ID, and contact email.",
)
def create_client(payload: ClientCreate):
    # Check for duplicate tax identifier
    existing = [c for c in db.get_all_clients() if c["tax_identifier"].lower() == payload.tax_identifier.lower()]
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A corporate client with Tax ID '{payload.tax_identifier}' is already registered.",
        )
    return db.add_client(payload.model_dump())


@router.patch(
    "/{client_id}",
    response_model=ClientResponse,
    summary="Update corporate client information",
    description="Update credit limit, contact email, status, or legal name for an existing client.",
)
def update_client(client_id: str, payload: ClientUpdate):
    client = db.get_client(client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with ID '{client_id}' does not exist.",
        )
    update_data = payload.model_dump(exclude_unset=True)
    client.update(update_data)
    return client
