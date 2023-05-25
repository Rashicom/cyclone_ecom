from django.urls import path,include
from . import views

urlpatterns = [
    path('', views.cycloneadmin_login, name="login"),
    path('dashboard/',views.cycloneadmin_dashboard.as_view(),name="dashboard"),
    path('userinfo/',views.cycloneadmin_userinfo,name="userinfo"),
    path('sellerinfo/',views.cycloneadmin_sellerinfo,name="sellerinfo"),
    path('products/',views.cycloneadmin_products,name="products"),
    path('category/',views.cycloneadmin_category,name = "category"),
    path('addcategory/',views.cycloneadmin_addcategory,name = "addcategory"),
    path('editcategory/<int:category_id>',views.cycloneadmin_editcategory,name = 'editcategory'),
    path('deletecategory/',views.cycloneadmin_delete_category.as_view(), name='deletecategory'),
    path('orders/',views.cycloneadmin_orders,name="orders"),
    path('reports/',views.cycloneadmin_reports,name="reports"),
    path('logout/',views.cycloneadmin_logout,name="logout"),
    path('addproduct/',views.cycloneadmin_addproduct.as_view(),name='addproduct'),
    path('editproduct/<int:product_id>',views.cycloneadmin_editproduct,name="editproduct"),
    path('deleteproduct/<int:product_id>',views.cycloneadmin_deleteproduct,name="deleteproduct"),
    path('edituseracces',views.cycloneadmin_edituseracces.as_view(),name="edituseracces"),
    path('coupenmanagemant/',views.cycloneadmin_coupenmanagemant.as_view(),name='coupenmanagemant'),
    path('offermanagement/',views.cycloneadmin_offer_management.as_view(),name='offermanagement'),
    path('addcoupen/',views.cyclone_addcoupen.as_view(),name='addcoupen'),
    path('addoffer/',views.cycloneadmin_add_offer.as_view(),name='addoffer'),
    path('deletecoupen/',views.cycloneadmin_deletecoupen.as_view(),name='deletecoupen'),
    path('orderupdation/',views.cycloneadmin_order_updation.as_view(),name='orderupdation'),
    path('cancelorder/', views.cycloneadmin_cancel_order.as_view(),name='cancelorder'),
    path('reportgenerator/',views.cycloneadmin_report_generator.as_view(),name="reportgenerator"),
    path('csvreportdownloader/', views.csv_report_downloader.as_view(), name="csvreportdownloader"),
    path('pdfreportdownloader/',views.pdf_report_downloader.as_view(), name="pdfreportdownloader")



]
