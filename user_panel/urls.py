from django.urls import path
from . import views

app_name = 'user_panel'

urlpatterns = [
    path('products/', views.UserPanelProductListView.as_view(), name='user_products'),
    path('product/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('product/<int:pk>/rate/', views.AddRatingView.as_view(), name='add_rating'),
    path('profile/edit/', views.EditProfileView.as_view(), name='edit_profile'),
    path('profile/change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('user-profile/', views.UserProfile.as_view(), name='user_profile'),
    path('add-to-wishlist/', views.AddToWishlistView.as_view(), name='add_to_wishlist'),
    path('wishlist/remove/<int:variant_id>/', views.RemoveFromWishlistView.as_view(), name='remove_from_wishlist'),
    path('wishlist/', views.WishlistListView.as_view(), name='wishlist'),
    path('toggle-wishlist/', views.toggle_wishlist, name='toggle_wishlist'),
    path('check-wishlist/', views.check_wishlist, name='check_wishlist'),
    path('invoice/<uuid:order_id>/download/', views.download_invoice, name='download_invoice'),
]

