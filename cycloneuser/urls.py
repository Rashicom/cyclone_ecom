from django.urls import path,include
from . import views

urlpatterns = [
    path('', views.cyclone_user.as_view(),name='user'),
    path('userlogout/',views.cyclone_userlogout.as_view(),name="userlogout"),
    path('addnewaddress/',views.cyclone_addnewaddress.as_view(),name='addnewaddress'),
    path('deleteaddress/',views.cyclone_deleteaddress.as_view(),name='deleteaddress'),
    path('forgotpassword/',views.cyclone_forgotpassword.as_view(),name='forgotpassword'),
    path('mobileotpgenerator/',views.cyclone_mobile_otp_generator.as_view(),name='mobileotpgenerator'),
    path('userorder/',views.cyclone_user_order.as_view(),name='userorder'),
    path('usercancelorder/',views.user_cancel_order.as_view(),name='usercancelorder'),
    path('userpasswordreset/',views.cyclone_user_password_reset.as_view(),name='userpasswordreset'),
    path('orderinvoicedownload/<str:order_no>',views.cyclone_order_invoice_download.as_view(), name='orderinvoicedownload'),
    path('mywallet',views.cyclone_my_wallet.as_view(),name='mywallet')
    

]