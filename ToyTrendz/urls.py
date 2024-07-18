from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('admin_panel/', include('admin_panel.urls')),
    path('category/', include('category.urls')),
    path('product/', include('product.urls')),
    path('brand/', include('brand.urls')),
    path('user_panel/', include('user_panel.urls')),
    path('cart/',include('cart.urls')),
    path('coupon/',include('coupon.urls')),
    path('order/',include('order.urls')),
    path('social-auth/', include('social_django.urls', namespace='social')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
