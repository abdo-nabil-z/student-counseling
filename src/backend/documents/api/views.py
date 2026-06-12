from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import status, serializers as drf_serializers
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiTypes, inline_serializer

from documents.models import Document, MasterDocument, MasterDocumentVersion
from documents.api.serializers import (
    MasterDocumentSerializer,
    MasterDocumentVersionSerializer,
)
from documents.services import  add_master_version


# ── Entity-bound documents ───────────────────────────────────────────────────

@extend_schema(
    responses={
        204: OpenApiResponse(description="Deleted"),
        404: OpenApiResponse(description="Not found"),
    },
    description="Delete a document and remove its file from storage.",
    tags=["Documents"],
)
@api_view(["DELETE"])
def delete_document(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    doc.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    responses={(200, "application/octet-stream"): OpenApiTypes.BINARY},
    description="Download the file for a document.",
    tags=["Documents"],
)
@api_view(["GET"])
def download_document(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    return FileResponse(doc.file.open("rb"), as_attachment=True, filename=doc.name)


# ── Master documents ─────────────────────────────────────────────────────────

@extend_schema(
    responses={200: MasterDocumentSerializer(many=True)},
    description="List all master documents, each including all versions and the latest version.",
    tags=["Documents"],
)
@api_view(["GET"])
def list_master_documents(request):
    masters = MasterDocument.objects.prefetch_related("versions").all()
    return Response(MasterDocumentSerializer(masters, many=True, context={"request": request}).data)


@extend_schema(
    request={"multipart/form-data": inline_serializer("MasterVersionUpload", fields={
        "file": drf_serializers.FileField(),
    })},
    responses={
        201: MasterDocumentVersionSerializer,
        400: OpenApiResponse(description="Validation errors"),
        404: OpenApiResponse(description="Master document not found"),
    },
    description="Upload a new version for a master document. The new version becomes the latest.",
    tags=["Documents"],
)
@api_view(["POST"])
@parser_classes([MultiPartParser])
def upload_master_version(request, pk):
    master = get_object_or_404(MasterDocument, pk=pk)
    file = request.FILES.get("file")
    if not file:
        return Response({"file": "This field is required."}, status=status.HTTP_400_BAD_REQUEST)
    version = add_master_version(master, file)
    return Response(MasterDocumentVersionSerializer(version, context={"request": request}).data, status=status.HTTP_201_CREATED)


@extend_schema(
    responses={(200, "application/octet-stream"): OpenApiTypes.BINARY},
    description="Download a specific version of a master document.",
    tags=["Documents"],
)
@api_view(["GET"])
def download_master_version(request, pk):
    version = get_object_or_404(MasterDocumentVersion, pk=pk)
    filename = version.file.name.split("/")[-1]
    return FileResponse(version.file.open("rb"), as_attachment=True, filename=filename)
