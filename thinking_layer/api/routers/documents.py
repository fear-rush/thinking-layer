from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies import get_document_service
from ..schemas.documents import DocumentBlockResponse, DocumentResponse
from ..services.documents import DocumentNotFoundError, DocumentService, DocumentStoreUnavailableError


router = APIRouter(prefix="/v1/documents", tags=["documents"])


def document_error(error: Exception) -> HTTPException:
    if isinstance(error, DocumentNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error))


@router.get("/{file_id}/blocks/{block_id}", response_model=DocumentBlockResponse)
def read_document_block(
    file_id: str,
    block_id: str,
    service: DocumentService = Depends(get_document_service),
) -> DocumentBlockResponse:
    try:
        return service.get_block(file_id, block_id)
    except (DocumentNotFoundError, DocumentStoreUnavailableError) as error:
        raise document_error(error) from error


@router.get("/{file_id}", response_model=DocumentResponse)
def read_document(
    file_id: str,
    service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    try:
        return service.get_document(file_id)
    except (DocumentNotFoundError, DocumentStoreUnavailableError) as error:
        raise document_error(error) from error
