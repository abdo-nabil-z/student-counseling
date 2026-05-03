from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view



@api_view(['POST','GET'])
def api_dummy(request):
    return Response({"message": "Hello from counselors API"}, status=status.HTTP_200_OK)