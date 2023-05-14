from django.urls import path,include
from . import views

urlpatterns = [
    path('', views.cycloneadmin_login, name="login"),
    path('dashboard/',views.cycloneadmin_dashboard,name="dashboard"),
    path('userinfo/',views.cycloneadmin_userinfo,name="userinfo"),
    path('sellerinfo/',views.cycloneadmin_sellerinfo,name="sellerinfo"),
    path('products/',views.cycloneadmin_products,name="products"),
    path('category/',views.cycloneadmin_category,name = "category"),
    path('addcategory/',views.cycloneadmin_addcategory,name = "addcategory"),
    path('editcategory/<int:category_id>',views.cycloneadmin_editcategory,name = 'editcategory'),
    path('orders/',views.cycloneadmin_orders,name="orders"),
    path('reports/',views.cycloneadmin_reports,name="reports"),
    path('logout/',views.cycloneadmin_logout,name="logout"),
    path('addproduct/',views.cycloneadmin_addproduct,name='addproduct'),
    path('editproduct/<int:product_id>',views.cycloneadmin_editproduct,name="editproduct"),
    path('deleteproduct/<int:product_id>',views.cycloneadmin_deleteproduct,name="deleteproduct"),
    path('edituseracces',views.cycloneadmin_edituseracces.as_view(),name="edituseracces"),
    path('coupenmanagemant/',views.coupenmanagemant.as_view(),name='coupenmanagemant'),
    path('addcoupen/',views.cyclone_addcoupen.as_view(),name='addcoupen')

]
