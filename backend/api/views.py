import csv
import hashlib

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .pagination import CustomPagination
from .permissions import AdminOrAuthorOrReadOnly
from .serializers import (
    CreateRecipeSerializer,
    IngredientSerializer,
    RecipeGetSerializer,
    ShoppingCartRecipeSerializer,
    TagSerializer
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    ShoppingCart,
    Tag
)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    search_fields = ['name']


class TagViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    filter_backends = (DjangoFilterBackend,)


class RecipeViewSet(viewsets.ModelViewSet):

    queryset = Recipe.objects.all()
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (AdminOrAuthorOrReadOnly,)

    def get_serializer_class(self):
        if self.request.method in 'GET':
            return RecipeGetSerializer
        return CreateRecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        permission_classes=(IsAuthenticated,),
        methods=('post', 'delete'),
        url_path='shopping_cart'
    )
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        author = self.request.user
        if request.method == 'POST':
            shopping_cart_exists = ShoppingCart.objects.filter(
                recipe=recipe,
                author=author
            ).exists()
            if not shopping_cart_exists:
                ShoppingCart.objects.create(recipe=recipe, author=author)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            serializer = ShoppingCartRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            obj = ShoppingCart.objects.filter(recipe=recipe, author=author)
            if not obj:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,),
        methods=['get'],
        url_path='download-shopping-cart'
    )
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart_items = ShoppingCart.objects.filter(author=user)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.csv"'
        )
        writer = csv.writer(response)
        writer.writerow(['Recipe', 'Ingredient'])
        for item in shopping_cart_items:
            recipe = item.recipe
            ingredients = recipe.ingredients.all()
            for ingredient in ingredients:
                writer.writerow([recipe.title, ingredient.name])

        return response

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)

        short_link_code = hashlib.md5(str(recipe.id).encode()).hexdigest()[:6]
        short_link = f'https://foodgram.example.org/s/{short_link_code}'

        return Response({'short-link': short_link}, status=status.HTTP_200_OK)

    @action(
        detail=True,
        permission_classes=(IsAuthenticated,),
        methods=('post', 'delete'),
        url_path='favorite'
    )
    def facorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        author = self.request.user
        if request.method == 'POST':
            favorite_exists = Favorite.objects.filter(
                recipe=recipe,
                author=author
            ).exists()
            if not favorite_exists:
                Favorite.objects.create(recipe=recipe, author=author)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            serializer = ShoppingCartRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            obj = Favorite.objects.filter(recipe=recipe, author=author)
            if not obj:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
