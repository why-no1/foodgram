from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from .utils import is_subscribed
from .models import Subscription, User
from recipes.models import Recipe
from .fields import Base64ImageField


class CustomUserSerializer(UserSerializer):

    avatar = Base64ImageField(required=False)
    is_subscribed = serializers.SerializerMethodField(
        method_name='get_is_subscribed'
    )

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

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return is_subscribed(request.user, obj)


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
        read_only_fields = ('email', 'username', 'first_name', 'last_name')

    def validate(self, data):
        author = data.get('author')
        user = data.get('user')
        if author == user:
            raise serializers.ValidationError(
                'Нельзя подписаться на самаого себя.'
            )
        return data

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return is_subscribed(request.user, obj)

    def get_recipes(self, obj):
        from api.serializers import ShoppingCartRecipeSerializer

        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[: int(limit)]
        serializer = ShoppingCartRecipeSerializer(
            recipes,
            many=True,
            read_only=True
        )
        return serializer.data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()


class SubscribeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscription
        fields = ['id', 'user', 'author']
