from django.urls import path
from .views import *
from . import views
app_name = 'user_panel'

urlpatterns = [
    path('products/', UserPanelProductListView.as_view(), name='user_products'),
    path('product/<int:pk>/', ProductDetailView.as_view(), name='product_detail'),
    path('product/<int:pk>/rate/', AddRatingView.as_view(), name='add_rating'),
    path('profile/edit/', EditProfileView.as_view(), name='edit_profile'),
    path('profile/change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('user-profile/', UserProfile.as_view(), name='user_profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('add-to-wishlist/', AddToWishlistView.as_view(), name='add_to_wishlist'),
    path('wishlist/remove/<int:variant_id>/', RemoveFromWishlistView.as_view(), name='remove_from_wishlist'),

    path('wishlist/', WishlistListView.as_view(), name='wishlist'),

]