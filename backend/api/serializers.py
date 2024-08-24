from rest_framework import serializers

from recipes.models import Ingredient, RecipeIngredient, Recipe, Tag
from users.serializers import Base64ImageField, CustomUserSerializer


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientsSerializer(serializers.ModelSerializer):

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeGetSerializer(serializers.ModelSerializer):

    author = CustomUserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientsSerializer(
        many=True,
        source='recipe_ingredients'
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'name', 'image',
            'text', 'cooking_time', 'is_favorited', 'is_in_shopping_cart'
        )

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return user.favorite.filter(recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return user.shopping_cart.filter(recipe=obj).exists()
        return False


class IngredientsAmountSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = Ingredient
        fields = ('id', 'amount')

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                'Количество ингредиента должно быть больше 0.'
            )
        return value


class CreateRecipeSerializer(serializers.ModelSerializer):

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientsAmountSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'tags', 'author', 'ingredients', 'name',
            'image', 'text', 'cooking_time'
        )

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError('Рецепт без ингредиентов.')

        for ingredient in value:
            if not Ingredient.objects.filter(id=ingredient['id']).exists():
                raise serializers.ValidationError(
                    f'Ингредиент {ingredient["id"]} не существует.'
                )

        ingredient_ids = set()
        for ingredient in value:
            ingredient_id = ingredient['id']
            if ingredient_id in ingredient_ids:
                raise serializers.ValidationError(
                    f'Ингредиент с ID {ingredient_id} уже добавлен.'
                )
            ingredient_ids.add(ingredient_id)
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError('Рецепт без Тегов.')

        for tag in value:
            if not Tag.objects.filter(name=tag).exists():
                raise serializers.ValidationError(
                    f'Данного тэга {tag} нет в списке доступных.'
                )

        set_value = set()
        for item in value:
            if item in set_value:
                raise serializers.ValidationError(
                    'Повторяющих тегов не должно быть.'
                )
            set_value.add(item)
        return value

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)

        if ingredients_data:
            for ingredient in ingredients_data:
                ingredient_id = ingredient['id']
                amount = ingredient['amount']
                ingredient = Ingredient.objects.get(id=ingredient_id)
                RecipeIngredient.objects.create(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=amount
                )

        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        instance.save()
        print(validated_data)
        if 'ingredients' in validated_data:
            ingredients_data = validated_data.pop('ingredients')
            print(ingredients_data)
            if ingredients_data:
                instance.ingredients.clear()

                for ingredient in ingredients_data:
                    ingredient_id = ingredient['id']
                    amount = ingredient['amount']
                    RecipeIngredient.objects.create(
                        recipe=instance,
                        ingredient_id=ingredient_id,
                        amount=amount
                    )
        else:
            raise serializers.ValidationError('Добавьте ингредиенты.')
        if 'tags' in validated_data:
            tags = validated_data.pop('tags', None)
            if tags:
                instance.tags.clear()
                instance.tags.set(tags)
        else:
            raise serializers.ValidationError('Добавьте теги.')

        return instance

    def to_representation(self, instance):
        return RecipeGetSerializer(
            instance, context={'request': self.context.get('request')}
        ).data


class ShoppingCartRecipeSerializer(serializers.ModelSerializer):

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
