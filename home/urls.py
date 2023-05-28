from django.urls import path,include
from . import views
from django.contrib.auth.decorators import login_required


urlpatterns = [
    path('',views.cyclone_home,name='home'),
    path('userlogin/',views.cyclone_login.as_view(),name='userlogin'),
    path('categories/',views.cyclone_category.as_view(),name='categories'),
    path('contact/',views.cyclone_contact.as_view(),name='contact'),
    path('blog/',views.cyclone_blog.as_view(),name='blog'),
    path('tracking/',views.cyclone_tracking.as_view(),name='tracking'),
    path('product/<int:category_id>',views.cyclone_product.as_view(),name='product'),
    path('productvarientselect/',views.product_varient_selector.as_view(), name='productvarientselect'),
    path('signup/',views.cyclone_signup.as_view(),name='signup'),
    path('otplogin/',views.cyclone_otplogin.as_view(),name='otplogin'),
    path('otpgenerator/',views.cyclone_otpgenerator.as_view(),name='otpgenerator'),
    path('addtowishlist/',views.cyclone_addtowishlist.as_view(),name='addtowishlist'),
    path('addtocart/',views.cyclone_addtocart.as_view(),name='addtocart'),
    path('wishlist/',views.cyclone_wishlist.as_view(),name='wishlist'),
    path('addcomment/',views.cyclone_add_comment.as_view(),name='addcomment'),
    path('addstarrate/',views.cyclone_add_star_rating.as_view(), name='addstarrate'),
    path('categoryfilter/',views.cyclone_category_filter.as_view(), name='categoryfilter'),
    path('contactadmin/',views.cyclone_contact_cyclone.as_view(), name='contactadmin'),
    path('tackorder/',views.cyclone_track_order.as_view(), name='tackorder'),
    path('mainsearch/',views.cyclone_main_search.as_view(),name='mainsearch')
    
]       