import os
from django.conf import settings
from django.views import static
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login, logout
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from .serializers import UserSerializer, GroupSerializer


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminUser, )
    queryset = User.objects.all()
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminUser, )
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def session_check(request):
    if request.user.is_authenticated():
        return Response(status=200)
    return Response(status=401)


@api_view(['POST'])
@permission_classes([AllowAny])
def session_login(request):
    data = JSONParser().parse(request)
    username = data.get('username')
    password = data.get('password')

    if username is None or password is None:
        return Response(status=400)

    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            login(request, user)
            return Response(status=200)
        else:
            return Response(status=403)
    return Response(status=401)


@api_view(['POST'])
@permission_classes([AllowAny])
def session_logout(request):
    logout(request)
    return Response(status=200)


def serve_angular_app(request, path):
    try:
        response = static.serve(
            request, path, document_root=os.path.join(settings.SERVICE_ROOT, 'angular_app', 'app'))
    except Exception:
        response = static.serve(
            request, '/index.html', document_root=os.path.join(settings.SERVICE_ROOT, 'angular_app', 'app'))
    return response
