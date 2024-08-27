from django.contrib import admin

from .models import (
    FavoriteRecipes,
    Ingredient,
    Recipe,
    ShoppingCartRecipes,
    Tag
)


admin.site.register(Recipe)
admin.site.register(Ingredient)
admin.site.register(Tag)
admin.site.register(FavoriteRecipes)
admin.site.register(ShoppingCartRecipes)
