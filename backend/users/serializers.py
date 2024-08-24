import base64

from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField

from .models import User, Subscription
from recipes.models import Recipe


class Base64ImageField(serializers.ImageField):

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class CustomUserSerializer(UserSerializer):

    avatar = Base64ImageField(required=False)
    is_subscribed = serializers.SerializerMethodField(method_name='get_is_subscribed')

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
        )

    def update(self, instance, validated_data):
        avatar_data = validated_data.pop('avatar', None)
        if avatar_data:
            format, imgstr = avatar_data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f'avatar.{ext}')
            instance.avatar.save(f'avatar.{ext}', data, save=True)
        return super().update(instance, validated_data)
    
    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user, author=obj
        ).exists()


class CustomUserCreateSerializer(UserCreateSerializer):

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )

class SubscriptionSerializer(serializers.ModelSerializer):

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )
        read_only_fields = ("email", "username", "first_name", "last_name")
    
    def validate(self, data):
        author = data.get('author')
        user = data.get('user')
        if author == user:
            raise serializers.ValidationError('Нельзя подписаться на самаого себя.')
        return data

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return Subscription.objects.filter(author=obj, user=request.user).exists()
        
    def get_recipes(self, obj):
        from api.serializers import ShoppingCartRecipeSerializer

        request = self.context.get("request")
        limit = request.GET.get("recipes_limit")
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[: int(limit)]
        serializer = ShoppingCartRecipeSerializer(recipes, many=True, read_only=True)
        return serializer.data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()

class SubscribeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscription
        fields = ['id', 'user', 'author']