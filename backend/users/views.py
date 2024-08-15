import base64

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Subscription, User
from .serializers import CustomUserSerializer, SubscriptionSerializer
from api.pagination import CustomPagination


class CustomUserViewSet(UserViewSet):

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action == 'me':
            return IsAuthenticated(),
        return super().get_permissions()

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, **kwargs):

        user = request.user
        author = get_object_or_404(User, id=self.kwargs.get('id'))
        subscription = user.subscribes.filter(author=author)

        if request.method == 'POST':
            serializer = SubscriptionSerializer(
                author, data=request.data, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            Subscription.objects.create(user=user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not subscription:
                return Response(
                    {'Ошибка': 'Подписка уже удалена.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """Возвращает список подписок пользователя."""

        queryset = User.objects.filter(subscribers__user=request.user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar'
    )
    def update_avatar(self, request, *args, **kwargs):
        user = request.user

        if request.method == 'PUT':
            if 'avatar' in request.data:
                file = request.data['avatar']
                format, imgstr = file.split(';base64,')
                ext = format.split('/')[-1]
                user.avatar = ContentFile(
                    base64.b64decode(imgstr),
                    name='temp.' + ext
                )
                user.save()
                avatar_url = (
                    request.build_absolute_uri(user.avatar.url)
                    if user.avatar else None
                )
                return Response({
                    'avatar': avatar_url},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            user.avatar.delete()
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
