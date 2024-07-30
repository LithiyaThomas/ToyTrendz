from django.urls import path
from . import views

urlpatterns = [

    # Category Offer URLs
    path('category-offers/', views.category_offer_list, name='category_offer_list'),
    path('category-offers/create/', views.category_offer_create, name='category_offer_create'),
    path('category-offers/<int:category_id>/update/', views.category_offer_update, name='category_offer_update'),
    path('category-offer/delete/<int:category_id>/', views.category_offer_delete, name='category_offer_delete'),


    # Referral Offer URLs
    path('referral-offers/', views.referral_offer_list, name='referral_offer_list'),
    path('referral-offers/create/', views.referral_offer_create, name='referral_offer_create'),
    path('referral-offers/<int:referral_id>/update/', views.referral_offer_update, name='referral_offer_update'),
    path('referral-offers/<int:referral_id>/delete/', views.referral_offer_delete, name='referral_offer_delete'),
]
