import base64

from django.core.files.base import ContentFile
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import User, Subscription
from .serializers import (
    CustomUserSerializer,
    SubscriptionSerializer
)
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
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            user.avatar.delete()
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='subscriptions'
    )
    def subscriptions(self, request):
        user = request.user
        subscribed_users = user.subscriptions.all()
        users = User.objects.filter(
            id__in=subscribed_users.values_list('author', flat=True)
        )
        page = self.paginate_queryset(users)
        serializer = SubscriptionSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='subscribe'
    )
    def subscribe(self, request, id=None):
        author = self.get_object()
        user = request.user

        if request.method == 'POST':
            if author == user:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            if Subscription.objects.filter(user=user, author=author).exists():
                return Response(
                    {'detail': 'Вы уже подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Subscription.objects.create(user=user, author=author)
            serializer = SubscriptionSerializer(
                author,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        else:
            try:
                subscription = Subscription.objects.get(
                    user=user,
                    author=author
                )
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Subscription.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)
