import logging

from django.http import FileResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import (
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
)
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    parser_classes,
)
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from consultation_backend.api_exceptions import (
    FileStorageUnavailable,
    StoredFileNotFound,
)
from consultation_backend.api_serializers import (
    APIErrorResponseSerializer,
)
from documents.api.serializers import (
    MasterDocumentSerializer,
    MasterDocumentVersionSerializer,
    MasterDocumentVersionUploadSerializer,
)
from documents.models import (
    Document,
    MasterDocument,
    MasterDocumentVersion,
)
from documents.services import add_master_version


logger = logging.getLogger(__name__)


def _open_stored_file(
    file_field,
    *,
    resource_type: str,
    resource_id: int,
):
    """
    Open a stored file and convert expected storage problems into
    controlled API exceptions.
    """
    if not file_field or not file_field.name:
        raise StoredFileNotFound(
            details={
                "resource_type": resource_type,
                "resource_id": resource_id,
            }
        )

    try:
        return file_field.open("rb")

    except FileNotFoundError as exc:
        logger.warning(
            (
                "Database record points to a missing "
                "stored file: resource_type=%s "
                "resource_id=%s"
            ),
            resource_type,
            resource_id,
        )

        raise StoredFileNotFound(
            details={
                "resource_type": resource_type,
                "resource_id": resource_id,
            }
        ) from exc

    except OSError as exc:
        logger.exception(
            (
                "Failed to open stored file: "
                "resource_type=%s resource_id=%s"
            ),
            resource_type,
            resource_id,
        )

        raise FileStorageUnavailable(
            details={
                "resource_type": resource_type,
                "resource_id": resource_id,
            }
        ) from exc


# -------------------------------------------------------------------------
# Entity-bound documents
# -------------------------------------------------------------------------


@extend_schema(
    responses={
        204: OpenApiResponse(
            description="Deleted"
        ),
        404: APIErrorResponseSerializer,
    },
    description=(
        "Delete a document and remove its file "
        "from storage after the database transaction commits."
    ),
    tags=["Documents"],
)
@api_view(["DELETE"])
def delete_document(
    request,
    pk,
):
    document = get_object_or_404(
        Document,
        pk=pk,
    )

    document.delete()

    return Response(
        status=status.HTTP_204_NO_CONTENT
    )


@extend_schema(
    responses={
        (
            200,
            "application/octet-stream",
        ): OpenApiTypes.BINARY,
        404: APIErrorResponseSerializer,
        503: APIErrorResponseSerializer,
    },
    description="Download the file for a document.",
    tags=["Documents"],
)
@api_view(["GET"])
def download_document(
    request,
    pk,
):
    document = get_object_or_404(
        Document,
        pk=pk,
    )

    file_handle = _open_stored_file(
        document.file,
        resource_type="document",
        resource_id=document.pk,
    )

    return FileResponse(
        file_handle,
        as_attachment=True,
        filename=document.name,
    )


# -------------------------------------------------------------------------
# Master documents
# -------------------------------------------------------------------------


@extend_schema(
    responses={
        200: MasterDocumentSerializer(
            many=True
        )
    },
    description=(
        "List all master documents, including "
        "all versions and the latest version."
    ),
    tags=["Documents"],
)
@api_view(["GET"])
def list_master_documents(request):
    master_documents = (
        MasterDocument.objects
        .prefetch_related("versions")
        .all()
    )

    serializer = MasterDocumentSerializer(
        master_documents,
        many=True,
        context={
            "request": request,
        },
    )

    return Response(serializer.data)


@extend_schema(
    request=MasterDocumentVersionUploadSerializer,
    responses={
        201: MasterDocumentVersionSerializer,
        400: APIErrorResponseSerializer,
        404: APIErrorResponseSerializer,
    },
    description=(
        "Upload a new version for a master document. "
        "The new version becomes the latest."
    ),
    tags=["Documents"],
)
@api_view(["POST"])
@parser_classes([MultiPartParser])
def upload_master_version(
    request,
    pk,
):
    master_document = get_object_or_404(
        MasterDocument,
        pk=pk,
    )

    serializer = (
        MasterDocumentVersionUploadSerializer(
            data=request.data
        )
    )
    serializer.is_valid(
        raise_exception=True
    )

    version = add_master_version(
        master=master_document,
        file=serializer.validated_data["file"],
    )

    response_serializer = (
        MasterDocumentVersionSerializer(
            version,
            context={
                "request": request,
            },
        )
    )

    return Response(
        response_serializer.data,
        status=status.HTTP_201_CREATED,
    )


@extend_schema(
    responses={
        (
            200,
            "application/octet-stream",
        ): OpenApiTypes.BINARY,
        404: APIErrorResponseSerializer,
        503: APIErrorResponseSerializer,
    },
    description=(
        "Download a specific version "
        "of a master document."
    ),
    tags=["Documents"],
)
@api_view(["GET"])
def download_master_version(
    request,
    pk,
):
    version = get_object_or_404(
        MasterDocumentVersion,
        pk=pk,
    )

    file_handle = _open_stored_file(
        version.file,
        resource_type=(
            "master_document_version"
        ),
        resource_id=version.pk,
    )

    filename = version.file.name.rsplit(
        "/",
        maxsplit=1,
    )[-1]

    return FileResponse(
        file_handle,
        as_attachment=True,
        filename=filename,
    )