from django.urls import path,include
from . import views
from django.contrib.auth.decorators import login_required
urlpatterns = [
    path('',views.cyclone_cart.as_view(),name='cart'),
    path('checkout/',views.cyclone_checkout.as_view(),name='checkout'),
    path('quantitycheck/',views.quantitycheck.as_view(),name='quantitycheck'),
    path('ordersummery/',views.cyclone_ordersummery.as_view(),name='ordersummery'),
    path('coupencheck/',views.cyclone_coupen_check.as_view(), name='coupencheck'),
    path('codplaceorder/',views.cyclone_cod_placeorder.as_view(),name='codplaceorder'),
    path('paymentsuccess/<int:order_no>',views.cyclone_payment_success.as_view(),name = "paymentsuccess"),
    path('codsuccess/<int:order_no>',views.cyclone_cod_success.as_view(),name='codsuccess')

]
