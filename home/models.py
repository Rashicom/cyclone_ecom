from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.sessions.models import Session

class CustomUserManager(BaseUserManager):

    # overriding user based authentication methord to email base authentiction
    def _create_user(self, email, password, **extra_fields):

        if not email:
            raise ValueError("The given mail must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


# custom customer for the cyclone user 
# extrafields are added to by inheriting the django user
class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(_("email address"), unique=True, primary_key=True)
    gender = models.CharField(max_length=50, choices=[('MALEL','MALE'),('FEMALE','FEMALE'),('OTHER','OTHER')])
    user_otp = models.CharField(max_length=10)
    contact_number = models.CharField(max_length=12)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

# user address: user have multiple addresses
# foreign key: mail, references: CustomUser
class user_address(models.Model):
    email = models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    address_type = models.CharField(max_length=50)
    address = models.CharField(max_length=50)
    place = models.CharField(max_length=50)
    district = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    zip_cod = models.IntegerField()
    contact_number = models.BigIntegerField()


# product table 
# primary key : product_id
class product(models.Model):
    product_id = models.AutoField(primary_key=True)
    model = models.CharField(max_length=50)
    company = models.CharField(max_length=50)
    bike_type = models.CharField(max_length=50, choices=[('mountain bike','mountain bike'),('roa dbik','road bike'),('hybrid','hybrid'),('kids bike','kids bike'),])
    wheel_size = models.IntegerField()
    suspention = models.CharField(max_length=50)
    internal_cabling = models.BooleanField(choices=[(True,'yes'),(False,'no')])
    gender_cat = models.CharField(max_length=50, choices=[('MALEL','MALE'),('FEMALE','FEMALE'),('UNISEX','UNISEX')])


# product_catogery table for different colors and other product categories
# forign : key product_id, reference: product table
class product_category(models.Model):
    product_id = models.ForeignKey(product,on_delete=models.CASCADE)
    frame_size = models.IntegerField()
    color = models.CharField(max_length=20)
    break_type = models.CharField(max_length=50)
    gear_type = models.CharField(max_length=80)
    mrp = models.IntegerField()
    seller_price = models.IntegerField()
    is_discounted = models.BooleanField(default=False)
    added_date = models.DateField(auto_now_add=True)
    quantity = models.IntegerField()

# for picture
# single category have many pictures
class product_image(models.Model):
    category_id = models.ForeignKey(product_category,on_delete=models.CASCADE)
    product_image = models.ImageField(upload_to = 'product_image')


# product description
# foreign key : product_id, reference : product table
class product_description(models.Model):
    product_id = models.ForeignKey(product,on_delete=models.CASCADE)
    terrain_description = models.TextField()
    strength_description = models.TextField()
    perfomance_description = models.TextField()
    precision_description = models.TextField()

# cart table
# forign key : mail from Customcustomer
# forign key : product_id from product
class cart_items(models.Model):
    category_id = models.ForeignKey(product_category,on_delete=models.CASCADE)
    email = models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    cartitem_quantity = models.IntegerField(default=1)

# wishlist table
# forign key : mail from Customcustomer
# forign key : product_id from product
class wishlist_items(models.Model):
    category_id = models.ForeignKey(product_category,on_delete=models.CASCADE)
    email = models.ForeignKey(CustomUser,on_delete=models.CASCADE)


# user order table
class user_order(models.Model):
    order_no = models.AutoField(primary_key=True)
    email = models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    order_date = models.DateField(auto_now=True)
    payment_method = models.CharField(max_length=50)
    payment_status = models.CharField(max_length=50)
    order_status = models.CharField(max_length=50)
    to_address = models.ForeignKey(user_address, on_delete=models.CASCADE)
    mrp_amount = models.IntegerField()
    seller_discount = models.IntegerField()
    coupen_discount = models.IntegerField(default=0)
    delivery_charge = models.IntegerField()
    payment_amount = models.IntegerField()

# user orders
class order_list(models.Model):
    order_no = models.ForeignKey(user_order,on_delete=models.CASCADE)
    category_id = models.ForeignKey(product_category, on_delete=models.CASCADE)


# user order list 
# one user can have multiple product in a single order
class product_review(models.Model):
    category_id = models.ForeignKey(product_category,on_delete=models.CASCADE)
    email = models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    review_date = models.DateField(auto_now=True)
    star_rank = models.IntegerField()
    product_comment = models.TextField()


"""<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<GUEST USER>>>>>>>>>>>>>>>>>>>>>>>>>>"""

# quest user cart 
# fk > session table and product category table
class guest_cart_items(models.Model):
    category_id = models.ForeignKey(product_category,on_delete=models.CASCADE)
    session_id = models.ForeignKey(Session,on_delete=models.CASCADE)
    cartitem_quantity = models.IntegerField(default=1)

# qust user whishlist
# fk > session table and product category table
class guest_wishlist_items(models.Model):
    category_id = models.ForeignKey(product_category,on_delete=models.CASCADE)
    session_id = models.ForeignKey(Session,on_delete=models.CASCADE)
    


"""<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<COUPEN MODEL>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"""

# discount_coupen
class discount_coupen(models.Model):
    coupen_no = models.CharField(max_length=50, primary_key=True)
    coupen_type = models.CharField(max_length=50)
    discount = models.IntegerField()
    expiry_date = models.DateField(auto_now=False, auto_now_add=False)


# applyed coupen
class applyed_coupen(models.Model):
    email = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    order_no = models.ForeignKey(user_order, on_delete=models.CASCADE)
    coupen_no = models.ForeignKey(discount_coupen, on_delete=models.CASCADE)


"""<<<<<<<<<<<<<<<<<<<<<seller>>>>>>>>>>>>>>>>>>>>>"""


# Create your models here.

