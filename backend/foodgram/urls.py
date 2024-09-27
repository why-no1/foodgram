from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from api.views import short_link


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls', namespace='api')),
    path('s/<str:pk>/', short_link, name='short_link'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
