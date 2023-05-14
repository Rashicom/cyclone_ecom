from django.contrib import admin

from home.models import CustomUser,product,product_category,product_image,product_description,wishlist_items,cart_items,user_address

admin.site.register(CustomUser)
admin.site.register(product)
admin.site.register(product_category)
admin.site.register(product_image)
admin.site.register(product_description)
admin.site.register(wishlist_items)
admin.site.register(cart_items)
admin.site.register(user_address)


# Register your models here.
