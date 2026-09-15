from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from legal.loader import get_public_document, public_catalog


class LegalDocumentListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        items = [
            {"slug": d["slug"], "title": d["title"], "version": d["version"]}
            for d in public_catalog().values()
        ]
        return Response({"documents": items})


class LegalDocumentDetailView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, slug: str):
        doc = get_public_document(slug)
        if not doc:
            return Response(
                {"error": {"code": "not_found", "message": "Документ не найден", "details": {}}},
                status=404,
            )
        return Response(doc)
