from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from home.models import CustomUser,product,product_category,product_description,wishlist_items,cart_items,product_image,guest_cart_items,guest_wishlist_items,product_review
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
import random
from django.contrib.sessions.models import Session
from django.http.response import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.views import View
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string

# Ai model for text sentiment
from textblob import TextBlob



# Create your views here.

# home page
def cyclone_home(request):
    """
    we have to fetch filtered data such as newly added feachered
    products offere products and so on to show in the main page
    which is home where user enter first
    """

    """<<<<<<<<<<<<feacherd producs>>>>>>>>>>>>>>>"""
    # fetching 3 products of different companies for featured product html area
    featured_pruducts = product_category.objects.order_by("product_id__company").distinct("product_id__company")[:3] 
    
    # appending product details and imagest tp products
    products = []
    for f_product in featured_pruducts:
        """
        image returns a query set which contains list of items
        so we need first image from firsl list([:1])
        for accessing first list data([0])
        for accessig the dict value ["product_image"]
        """
        image = product_image.objects.filter(category_id = f_product).values("product_image")[:1][0]["product_image"]
        products.append({"category_id":f_product.id,"model":f_product.product_id.model,"seller_price":f_product.seller_price,"mrp":f_product.mrp,"image":image})
    

    """<<<<<<<<<<<<new 5 producs>>>>>>>>>>>>>>>"""

    # fetching first 5 newly added items
    firstfive_products = product_category.objects.order_by("added_date")[:5]
    
    # appending new product details and imagest tp new products table
    new_products = []
    for n_product in firstfive_products:
        """
        image returns a query set which contains list of items
        so we need first image from firsl list([:1])
        for accessing first list data([0])
        for accessig the dict value ["product_image"]
        """
        image = product_image.objects.filter(category_id = n_product).values("product_image")[:1][0]["product_image"]
        new_products.append({"category_id":n_product.id,"model":n_product.product_id.model,"seller_price":n_product.seller_price,"mrp":n_product.mrp,"image":image})
    
    # popoing first product(most new produt) from 5 product to show it seperately in html
    # rest of the list size is 4 now
    first_product = new_products.pop(0)


    """<<<<<<<<<<<<most rated 8 producs>>>>>>>>>>>>>>>"""

    # fetching most rated 8 products (need to compleate)
    # now just fetching random products
    rated_pruducts = product_category.objects.all()
    
    # appending product details and imagest tp products
    most_rated_products = []
    for r_product in rated_pruducts:
        """
        image returns a query set which contains list of items
        so we need first image from firsl list([:1])
        for accessing first list data([0])
        for accessig the dict value ["product_image"]
        """
        image = product_image.objects.filter(category_id = r_product).values("product_image")[:1][0]["product_image"]
        most_rated_products.append({"category_id":r_product.id,"model":r_product.product_id.model,"seller_price":r_product.seller_price,"mrp":r_product.mrp,"image":image})
    
    return render(request,'cyclone_home.html',{"products":products, "new_products":new_products,"first_product":first_product,"most_rated_products":most_rated_products})



class cyclone_login(View):

    def post(self,request):
        """
        before login the user must be a guest user, so we have to 
        check any item added to cart or wishlist as a gust user
        so we have to move all those items to users listwe are checking 
        and exicuting the item transfer code just after checking the 
        user creation and befor login, after the login the session id 
        will be replaced and we cant the guest user table
        """
        
        # fetching cedencials from request
        email = request.POST["email"]
        password = request.POST["password"]
        # validating the user is exixt or not
        
        user = authenticate(email = email, password = password)
        if user is not None:
            """
            before login we have to fetch all items from cart and wishlist 
            if any as a qust user
            """
                
            try:
                # fetching guest user instence
                session_id = request.session.session_key
                guestuser_instence = Session.objects.get(session_key = session_id)
                    
                # fetching newly create user instence
                user_instence = CustomUser.objects.get(email = email)

                # fetching guest cart items list and wishlist items
                guest_cartitems = guest_cart_items.objects.filter(session_id = guestuser_instence)
                guest_wishlist = guest_wishlist_items.objects.filter(session_id = guestuser_instence)
                    
                # transfering to user cart list
                for cart_item in guest_cartitems:
                    new_cartitem = cart_items(email = user_instence, category_id = cart_item.category_id, cartitem_quantity = cart_item.cartitem_quantity )
                    new_cartitem.save()

                # transfering to user wish list
                for wish_item in guest_wishlist:
                    new_wishitem = wishlist_items(email = user_instence, category_id = wish_item.category_id)
                    new_wishitem.save()
                
                if request.session.get('guest_user_cartredirect'):
                    login(request,user)
                    return redirect("cart")

            except Exception:
                print("exception found")
                login(request,user)
                return redirect("user")

            login(request,user)
            return redirect("user")
        else:
            messages.info(request,"User not found")
            return redirect("userlogin")
    
    def get(self,request):
        
        # if methord is get
        return render(request,'cyclone_login.html')
                 
    
    


# generate otp and send to mail
class cyclone_otpgenerator(View):

    def post(self,request):
        print("otp generator")
        email = request.POST['email']
    
        # if the user not found return not found mssg 
        try:
            user = CustomUser.objects.get(email = email)
        except CustomUser.DoesNotExist:
            return JsonResponse({'status':'user not found'})
    
        if not user.is_active:
            return JsonResponse({'status':'Unautherized user'})
        
        otp = random.randint(1000,9999)
        user.user_otp = otp
        user.save()

        # send otp to email
        subject = 'cyclone OTP'
        message = 'Hello there! your OTP'+str(otp)
        recipient = email
        send_mail(subject,message,settings.EMAIL_HOST_USER,[recipient],fail_silently=False)
        return JsonResponse({'status':'otp send to mail'})


        

# email otp varify and login
class cyclone_otplogin(View):
    
    def post(self,request):
        # validate the otp
        email = request.POST['email']
        otp = request.POST['otp']
        user = CustomUser.objects.get(email = email)

        # check the otp is matching or not
        if user.user_otp == otp:
            # delete otp from field
            login(request,user)
            return redirect("user")
        else:
            messages.info(request,"invalied otp")
    
    def get(self,request):
        # if the request is get
        return render(request,'cyclone_otplogin.html')


class cyclone_category(View):
    
    def get(self,request):

        # products = product.objects.values("product_category__id","product_id","model","suspention","product_category__break_type","product_category__gear_type","product_category__mrp","product_category__is_discounted","product_category__seller_price","product_category__product_image__product_image")
        cart_products =  product_category.objects.all()

        cart_items = []
        for item in cart_products:
            category_id = item.id
            color = item.color
            break_type = item.break_type
            gear_type = item.gear_type
            mrp = item.mrp
            seller_price = item.seller_price
            is_discounted = item.is_discounted
            model = item.product_id.model
            suspention = item.product_id.suspention
            image = product_image.objects.filter(category_id = item).values("product_image")[:1][0]["product_image"]
            cart_items.append({"category_id":category_id, "color":color,"break_type":break_type,"gear_type":gear_type,"mrp":mrp,"seller_price":seller_price,"is_discounted":is_discounted,"model":model,"suspention":suspention,"image":image})

        return render(request,'cyclone_category.html',{'cart_items':cart_items})


            

class cyclone_contact(View):
    def get(self,request):
        return render(request,'cyclone_contact.html')

class cyclone_blog(View):

    def get(self,request):
        return render(request,'cyclone_blog.html')

class cyclone_tracking(View):
    def get(self,request):
        return render(request,'cyclone_tracking.html')
    

class cyclone_product(View):

    def get(self,request,**kwargs):
        category_id = kwargs['category_id'] 
        product_details = product_category.objects.get(id = category_id)
        
        product_instence = product_details.product_id
        product_dscpn = product_description.objects.get(product_id = product_instence)
        product_first_pic = product_image.objects.filter(category_id = product_details).values('product_image')[:1][0]['product_image']
        product_pics = product_image.objects.filter(category_id = product_details)[1:]
        product_reviews = product_review.objects.filter(category_id = product_details).values('star_rank','product_comment','review_date','email__first_name')
        
        return render(request,'cyclone_product.html',{"product_details":product_details,'product_dscpn':product_dscpn,'product_pics':product_pics,'product_first_pic':product_first_pic,'category_id':category_id,"product_reviews":product_reviews})



# signup
class cyclone_signup(View):

    def post(self,request):

        # fetching the signup data
        email = request.POST["email"]
        password1 = request.POST["password1"]
        password2 = request.POST["password2"]
        # password matching need tobe checked in the frontend
        # already check the emaile exist or not when curser leave using ajax

        user = CustomUser.objects.create_user(email=email,password=password1)
        return   redirect('userlogin')
    
    def get(self,request):
        return render(request,'cyclone_signup.html')


# add to wishlist ajax call
class cyclone_addtowishlist(View):

    
    def post(self,request):

        category_id = request.POST['category_id']

        # if quest user
        if not request.user.is_authenticated:
            session_id = request.session.session_key
            
            # if no session, we create a session to uniqely identify the user
            if session_id is None:
                request.session.create()
            
            # fetch info to add item to wishlist
            guest_category_instence = product_category.objects.get(id=category_id)
            guest_user_instence = Session.objects.get(session_key = request.session.session_key)
            
            # if product already exixt in wishlist
            if guest_wishlist_items.objects.filter(category_id = guest_category_instence, session_id = guest_user_instence).exists():
                
                # remove from wishlist
                print("category exist in guest wishlist")
                guest_wishlist_items.objects.filter(category_id = guest_category_instence,session_id = guest_user_instence).delete()
                return JsonResponse({'status':200,'message':'item removed from guest wishlist'})
            
            # if product not exist in guest wishlist
            else:
                
                # add item to guest cart
                new_guest_wishitem = guest_wishlist_items(category_id = guest_category_instence, session_id = guest_user_instence)
                new_guest_wishitem.save()
                return JsonResponse({'status':200,'message':'item added to guest wishlist'})

        
        email = request.user.email

        # fetching appropriate instence of the user and category
        category_instence = product_category.objects.get(id=category_id)
        user_instence = CustomUser.objects.get(email=email)
        
        # checking the item is already is in wishlist or not
        # adding if only item not in list else remove from wishlist
        if wishlist_items.objects.filter(category_id = category_id).exists():

            # remove from wishlist
            print("category exist in wishlist")
            wishlist_items.objects.filter(category_id = category_id).delete()
            return JsonResponse({'status':200,'message':'item removed from wishlist'})
        else:

            # add to wishlist table
            newwishitem = wishlist_items(category_id = category_instence, email = user_instence)
            newwishitem.save()
            return JsonResponse({'status':200,'message':'item added to wishlist'})
        


    # if user not signed in
    # need clarification
    """we use get becouse its carring only product"""
    def get(self,request):

        # if user not signed inn
        """
        we have to store the wish list items 
        in a temp position        
        """
        pass


#add to cart ajax call
class cyclone_addtocart(View):
    
    
    def post(self,request):
        """
        if anonimous user try to add items to cart we create a uneque id for
        the user and store cart items data in the quest_cart_items table
        """
        print("call to add to ccart")
        category_id = request.POST['category_id']
        # if quest user
        if not request.user.is_authenticated:
            session_id = request.session.session_key

            # if no session, we create a session to uniqely identify the user
            if session_id is None:
                request.session.create()
            
            # fetch info to add item to cart
            guest_category_instence = product_category.objects.get(id=category_id)
            guest_user_instence = Session.objects.get(session_key = request.session.session_key)
            
            # if product already exixt in cart
            if guest_cart_items.objects.filter(category_id = guest_category_instence, session_id = guest_user_instence).exists():
                
                # remove from wishlist
                print("category exist in guest cart")
                guest_cart_items.objects.filter(category_id = guest_category_instence,session_id = guest_user_instence).delete()
                return JsonResponse({'status':200,'message':'item removed from cart'})
            
            # if product not exist in guest cart
            else:

                # add item to guest cart
                new_guest_cartitem = guest_cart_items(category_id = guest_category_instence, session_id = guest_user_instence)
                new_guest_cartitem.save()
                return JsonResponse({'status':200,'message':'item added to cart'})


        # if authenticated user
        email = request.user.email

        # fetching appropriate instence of the user and category
        category_instence = product_category.objects.get(id=category_id)
        user_instence = CustomUser.objects.get(email=email)

        # checking the item is already is in cart or not
        # adding if only item not in list else remove from cart
        if cart_items.objects.filter(category_id = category_id, email = user_instence).exists():
            
            # remove from wishlist
            print("category exist in cart")
            cart_items.objects.filter(category_id = category_id, email = user_instence).delete()
            return JsonResponse({'status':200,'message':'item removed from cart'})

        else:

            # add to cart table
            newcartitem = cart_items(category_id = category_instence, email = user_instence)
            newcartitem.save()
            return JsonResponse({'status':200,'message':'item added to cart'})
        

    def get(self,request):

        # if user not signed inn
        """
        we have to store the wish list items 
        in a temp position        
        """
        pass


class cyclone_wishlist(View):

    def post(self,request):
        pass

    def get(self,request):

        # if guest user
        if not request.user.is_authenticated:
            session_id = request.session.session_key

            # if no session, we create a session to uniqely identify the user
            if session_id is None:
                request.session.create()

            # wishlist items fetching from gust wish list
            guest_user_instence = Session.objects.get(session_key = request.session.session_key)
            wishlistitems = guest_wishlist_items.objects.filter(session_id = guest_user_instence)
        
        # if autherized user
        else:
            # wishlist items fetching from user wish list
            email = request.user.email
            wishlistitems = wishlist_items.objects.filter(email = email)
        
        # fetch and append values to an array which we are gonna render
        wishlist_data = []
        for item in wishlistitems:
            product_cat = product_category.objects.get(id = item.category_id.id)
            produc = product.objects.get(product_id = product_cat.product_id.product_id)
            image = product_image.objects.filter(category_id = product_cat.id)[:1][0]
            wishlist_data.append({'company':produc.company,'model':produc.model,'category_id':item.category_id.id,'color':product_cat.color,'frame_size':product_cat.frame_size,'break_type':product_cat.break_type,'gear_type':product_cat.gear_type,'suspention':produc.suspention,'price':product_cat.seller_price,'image':image.product_image})   
        
        return render(request,'cyclone_wishlist.html',{'wishlist_data':wishlist_data})  


class cyclone_add_comment(View):

    def post(self, request):
        
        # fetching info of comment comment user and product_id
        email = request.user.email
        user_instence = CustomUser.objects.get(email = email)
        category_id = request.POST['category_id']
        category_instence = product_category.objects.get(id = category_id)
        comment = request.POST['comment']
        
        # usign textblob ai analyze coment behaviour
        # and generate a auto star rank fot the product
        """
        blob is returning polarity and subjuctivity. the polarity is 
        a value between -1 and +1 represnt the behaviour of the comment
        we are converting the value to a ranking scale number between 0 and 5
        """
        #  make an object and correct the speling mistakes
        blob = TextBlob(comment).correct()
        polarity = blob.polarity

        # converting to ranking scale number between 0 and 5
        rank =  int(((polarity+1)/2)*5)
        
        # update comment table
        new_review = product_review(category_id = category_instence, email = user_instence, star_rank = rank, product_comment = comment)
        new_review.save()
        
        return JsonResponse({'status':200,'message':'comment updatd'})


    
class cyclone_category_filter(View):

    def post(self, request):
        """
        fetching list of info from the ajax request
        to filter both list containing its filter 
        values
        """
        # fetch list from request
        bike_types = request.POST.getlist('bike_type[]')
        brands = request.POST.getlist('brand[]')
        colors = request.POST.getlist('color[]')
        price_filtered_val = request.POST.getlist('price_filtered_val[]')
        """
        fetch the products from the data base by applaying these
        array of filteres. every list contains. its mutliple filter values
        eg: color list contains multiple colors to filter
        """ 
        # fetch data from data base by applaying this list of filters
        cart_products =  product_category.objects.all()

        # filter by list of data
        if len(bike_types) > 0:
            cart_products = cart_products.filter(product_id__bike_type__in = bike_types)
        
        if len(brands) > 0:
            cart_products = cart_products.filter(product_id__company__in = brands)
        
        if len(colors) > 0:
            cart_products = cart_products.filter(color__in = colors)

        if len(price_filtered_val) > 0: 
            if price_filtered_val == '6':
                cart_products = cart_products.filter(seller_price__gte = int(price_filtered_val[0])*10000)
            else:
                cart_products = cart_products.filter(seller_price__lte = int(price_filtered_val[0])*10000)
                
        # creating a list of requred field for response from filtered data
        cart_items = []
        for item in cart_products:
            category_id = item.id
            color = item.color  
            break_type = item.break_type
            gear_type = item.gear_type
            mrp = item.mrp
            seller_price = item.seller_price
            is_discounted = item.is_discounted
            model = item.product_id.model
            suspention = item.product_id.suspention
            image = product_image.objects.filter(category_id = item).values("product_image")[:1][0]["product_image"]
            cart_items.append({"category_id":category_id, "color":color,"break_type":break_type,"gear_type":gear_type,"mrp":mrp,"seller_price":seller_price,"is_discounted":is_discounted,"model":model,"suspention":suspention,"image":image})


        print(cart_items)
        render_html = render_to_string('filter_category.html', {'cart_items':cart_items})
        return JsonResponse({'status':200,'html':render_html})