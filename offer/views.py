from django.shortcuts import render, get_object_or_404, redirect
from .models import  CategoryOffer, ReferralOffer
from .forms import  CategoryOfferForm, ReferralOfferForm
from django.views.decorators.http import require_POST
# Create your views here.



#
# #Product Offer
#
# def product_offer_list(request):
#     offers = ProductOffer.objects.all()
#     return render(request, 'offer/product_offer_list.html', {'offers': offers})
#
# def product_offer_create(request):
#     if request.method == 'POST':
#         form = ProductOfferForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('product_offer_list')
#     else:
#         form = ProductOfferForm()
#     return render(request, 'offer/product_offer_create.html', {'form': form})
#
# def product_offer_update(request, product_id):
#     offer = get_object_or_404(ProductOffer, id=product_id)
#     if request.method == 'POST':
#         form = ProductOfferForm(request.POST, instance=offer)
#         if form.is_valid():
#             form.save()
#             return redirect('product_offer_list')
#     else:
#         form = ProductOfferForm(instance=offer)
#     return render(request, 'offer/product_offer_edit.html', {'form': form})
#
# def product_offer_delete(request, product_id):
#     offer = get_object_or_404(ProductOffer, id=product_id)
#     if request.method == 'POST':
#         offer.delete()
#         return redirect('product_offer_list')

# Category Offer

def category_offer_list(request):
    offers = CategoryOffer.objects.all()
    return render(request, 'offer/category_offer_list.html', {'offers': offers})

def category_offer_create(request):
    if request.method == 'POST':
        form = CategoryOfferForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('category_offer_list')
    else:
        form = CategoryOfferForm()
    return render(request, 'offer/category_offer_create.html', {'form': form})

def category_offer_update(request, category_id):
    offer = get_object_or_404(CategoryOffer, id=category_id)
    if request.method == 'POST':
        form = CategoryOfferForm(request.POST, instance=offer)
        if form.is_valid():
            form.save()
            return redirect('category_offer_list')
    else:
        form = CategoryOfferForm(instance=offer)
    return render(request, 'offer/category_offer_edit.html', {'form': form})

@require_POST
def category_offer_delete(request, category_id):
    offer = get_object_or_404(CategoryOffer, id=category_id)
    offer.delete()
    return redirect('category_offer_list')

#Referral Offer

def referral_offer_list(request):
    offers = ReferralOffer.objects.all()
    return render(request, 'offer/referral_offer_list.html', {'offers': offers})

def referral_offer_create(request):
    if request.method == 'POST':
        form = ReferralOfferForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('referral_offer_list')
    else:
        form = ReferralOfferForm()
    return render(request, 'offer/referral_offer_create.html', {'form': form})

def referral_offer_update(request, referral_id):
    offer = get_object_or_404(ReferralOffer, id=referral_id)
    if request.method == 'POST':
        form = ReferralOfferForm(request.POST, instance=offer)
        if form.is_valid():
            form.save()
            return redirect('referral_offer_list')
    else:
        form = ReferralOfferForm(instance=offer)
    return render(request, 'offer/referral_offer_edit.html', {'form': form})

def referral_offer_delete(request, referral_id):
    offer = get_object_or_404(ReferralOffer, id=referral_id)
    if request.method == 'POST':
        offer.delete()
        return redirect('referral_offer_list')
