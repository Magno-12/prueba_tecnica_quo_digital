from django.urls import path, include

from rest_framework.routers import DefaultRouter

from apps.belvo.views.belvo_view import BelvoAPIViewSet

app_name = 'belvo'

router = DefaultRouter()
router.register(r'', BelvoAPIViewSet, basename='belvo')

urlpatterns = [
    path('', include(router.urls)),
]
