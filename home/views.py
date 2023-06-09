from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from home.models import CustomUser,product,product_category,product_description,wishlist_items,cart_items,product_image,guest_cart_items,guest_wishlist_items,product_review, user_order, subscription, user_wallet_account
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
import random
from django.contrib.sessions.models import Session
from django.http.response import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.views import View
from django.db.models import Avg
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin

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
            average_star_rating = product_review.objects.filter(category_id = item.id).aggregate(Avg('star_rank'))['star_rank__avg']
            
            # fetching same producs corol variations
            avilable_colors = product_category.objects.filter(product_id = item.product_id).values('color')
            
            # calculating offer percentage
            offer_percent = int(((mrp-seller_price)/mrp)*100)
            
            # if there no star rating found we put a defoult value 2 as default
            if average_star_rating is None:
                average_star_rating = 2
            cart_items.append({"category_id":category_id, "color":color,"break_type":break_type,"gear_type":gear_type,"mrp":mrp,"seller_price":seller_price,"is_discounted":is_discounted,"model":model,"suspention":suspention,"image":image,"average_star_rating":int(average_star_rating), "avilable_colors":avilable_colors,"offer_percent":offer_percent})

        return render(request,'cyclone_category.html',{'cart_items':cart_items})


            

class cyclone_contact(View):
    def get(self,request):
        return render(request,'cyclone_contact.html')

class cyclone_blog(View):

    def get(self,request):
        return render(request,'cyclone_blog.html')

class cyclone_tracking(LoginRequiredMixin,View):
    login_url = "userlogin"

    def get(self,request):
        return render(request,'cyclone_tracking.html')
    

class cyclone_product(View):

    def get(self,request,**kwargs):
        category_id = kwargs['category_id'] 
        product_details = product_category.objects.get(id = category_id)

        # calculating product discount percentage
        is_discounted = product_details.is_discounted
        if is_discounted:
            is_discounted = int(((product_details.mrp-product_details.seller_price)/product_details.mrp)*100)
        
        product_instence = product_details.product_id
        product_dscpn = product_description.objects.get(product_id = product_instence)
        product_first_pic = product_image.objects.filter(category_id = product_details).values('product_image')[:1][0]['product_image']
        product_pics = product_image.objects.filter(category_id = product_details)[1:]
        product_reviews = product_review.objects.filter(category_id = product_details).values('star_rank','product_comment','review_date','email__first_name')
        average_star_rating = product_review.objects.filter(category_id = category_id).aggregate(Avg('star_rank'))['star_rank__avg']
        product_color = product_details.color
        product_frame_size = product_details.frame_size 
        
        """
        fetching available color and size of the products also to display
        its id also fetched to uniquely pass the id with it, and it helps 
        to find that item when user click to that veleint 
        """
        # fetching all available colors in this product
        available_colors = product_category.objects.filter(product_id = product_details.product_id).values('color').exclude(color = product_color).distinct()

        # fetching all available sizes in this product
        available_sizes = product_category.objects.filter(product_id = product_details.product_id).values('frame_size').exclude(frame_size = product_frame_size).distinct()
        
        # if there no star rating found we put a defoult value 2 as default
        if average_star_rating is None:
            average_star_rating = 2

        return render(request,'cyclone_product.html',{"product_details":product_details,'product_dscpn':product_dscpn,'product_pics':product_pics,'product_first_pic':product_first_pic,'category_id':category_id,"product_color":product_color,"product_frame_size":product_frame_size,"product_reviews":product_reviews,"average_star_rating":int(average_star_rating),"available_colors":available_colors,"available_sizes":available_sizes,"is_discounted":is_discounted})



# signup
class cyclone_signup(View):

    def post(self,request):

        # fetching the signup data
        email = request.POST["email"]
        password1 = request.POST["password1"]
        password2 = request.POST["password2"]
        # password matching need tobe checked in the frontend
        # already check the emaile exist or not when curser leave using ajax

        # creating user
        user = CustomUser.objects.create_user(email=email,password=password1)

        # initialize user wallet with 0 balance
        # defultly amoumt set to zeto
        new_wallet = user_wallet_account(email = user)
        new_wallet.save()

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



# product commenting
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
        
        # check if there any comment or star rating alredy exist
        new_review_exixts = product_review.objects.filter(email = user_instence, category_id = category_id)
        
        # if user alredy commented or stare rated update it
        if new_review_exixts:
            new_review = product_review.objects.get(email = email, category_id = category_id)
            new_review.star_rank = rank
            new_review.product_comment = comment
            new_review.save()
        
        # else create new one
        else:
            new_review = product_review(category_id = category_instence, email = user_instence, star_rank = rank, product_comment = comment)
            new_review.save()
        
        # fetching commetns to refresh 
        product_reviews = product_review.objects.filter(category_id = category_id).values('star_rank','product_comment','review_date','email__first_name')

        review_part_html = render_to_string('review_part.html', {"product_reviews":product_reviews})
        return JsonResponse({'status':200,'message':'comment updatd',"review_part_html":review_part_html})


# star rating
class cyclone_add_star_rating(View):

    def post(self, request):
        """
        add the star rating if there is no rating and update if the user
        already rated befor
        """

        # fetching data and creatintin user instance to update star rating
        star_rate_value = request.POST['star_rate_value']
        category_id = request.POST['category_id']
        email = request.user.email
        category_instance = product_category.objects.get(id = category_id)
        user_instance = CustomUser.objects.get(email = email)

        # checking the user already commented or star rated
        new_review_exist = product_review.objects.filter(email = user_instance, category_id = category_id).exists()
        
        # if review exists update
        if new_review_exist:
            new_review = product_review.objects.get(email = user_instance, category_id = category_id)
            new_review.star_rank = star_rate_value
            new_review.save()
        
        # else review not excist, create one without any comment
        else:
            new_review = product_review(email = user_instance, category_id = category_instance, star_rank = star_rate_value)
            new_review.save()

        # fetching commetns to refresh 
        product_reviews = product_review.objects.filter(category_id = category_id).values('star_rank','product_comment','review_date','email__first_name')

        review_part_html = render_to_string('review_part.html', {"product_reviews":product_reviews})

        # update table to new star rating
        return JsonResponse({'status':200,'message':'your rating has been recorded',"review_part_html":review_part_html })



# category filter ajax request   
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
        print(bike_types)
        print(cart_products)
        
        # filter by list of data
        if len(bike_types) > 0:
            cart_products = cart_products.filter(product_id__bike_type__in = bike_types)
        print(cart_products)
        if len(brands) > 0:
            cart_products = cart_products.filter(product_id__company__in = brands)
        
        if len(colors) > 0:
            cart_products = cart_products.filter(color__in = colors)

        # filter by price filter
        if len(price_filtered_val) > 0: 
            """
            the price values comes in a list. the list value contains only one value
            we can pass this as a string, but we pass it as a list even it contains only
            one value inorder to simplify the filtering process. all the other values are
            passing like list, but in contains multiple values. price scale value between
            1 and 6. so we have to multiply by 10000 to perform filter. and inorder to fetch 
            the first value from the list we use [0].
            """

            if price_filtered_val == '6':
                cart_products = cart_products.filter(seller_price__gte = int(price_filtered_val[0])*10000)
            else:
                cart_products = cart_products.filter(seller_price__lte = int(price_filtered_val[0])*10000)

        # filtered rows go through the for loop to fetch need info only from it    
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
            average_star_rating = product_review.objects.filter(category_id = item.id).aggregate(Avg('star_rank'))['star_rank__avg']
            
            # fetching same producs corol variations
            avilable_colors = product_category.objects.filter(product_id = item.product_id).values('color')

            # if there no star rating found we put a defoult value 2 as default
            if average_star_rating is None:
                average_star_rating = 2

            # appdending all the needed info to the cart_items list as a dict
            cart_items.append({"category_id":category_id, "color":color,"break_type":break_type,"gear_type":gear_type,"mrp":mrp,"seller_price":seller_price,"is_discounted":is_discounted,"model":model,"suspention":suspention,"image":image,"average_star_rating":average_star_rating,"avilable_colors":avilable_colors})

        """
        filter_category.html is a small part of html that we have to change in the main page
        so compaign this part html by the filtered data using render_to_string function
        this is how we pass html through a jason respose.
        this part of html reach in the fromt end ajax success and update the part of html
        """
        # compaingning part of html and data
        
        render_html = render_to_string('filter_category.html', {'cart_items':cart_items})
        # json responce to ajax request
        return JsonResponse({'status':200,'html':render_html})
        


# order tracking
class cyclone_track_order(LoginRequiredMixin,View):
    login_url = "userlogin"

    def get(self, requset):
        email = requset.user.email
        order_id = requset.GET['order_id']
        order_detailes = user_order.objects.get(order_no = order_id, email = email)
        
        return JsonResponse({'status':200, "order_id":order_detailes.order_no, "order_status":order_detailes.order_status, "payment_status":order_detailes.payment_status}) 



# cantact page send email
class cyclone_contact_cyclone(View):

    def post(self, request):

        # fetching data
        name = request.POST['name']
        email = request.POST['email']
        subject = request.POST['subject']
        message = request.POST['message']

        return JsonResponse({'status':200})


# search auto suggestion
class cyclone_auto_suggestion(View):

    def get(self, request):
        """
        a aja erquest carrieng the requested for value and return the 
        company or order names which matches for the search value
        """

        # fetching seatch for data
        search_for = request.GET['search_for']
        
        # searching in the data set for match as search suggestion 
        """
        searching for search_for in company, model and bike type also. list() is used for returning list
        insted of query set. _istartswith is for searching starts with that search_for and __i represending case insensitive.
        distinct() make sure that no duplicates are there. value_list returning only the fields specified as the parameter not the 
        object and return it as a tuple. flat = true converts the tuple in to list values if it contains only one colomn items
        """

        # searching for company name
        suggestion_result = list(product_category.objects.filter(
            Q(product_id__company__istartswith = search_for)).distinct().values_list("product_id__company",flat=True))

        #searching for model name and add to the previous search suggestion
        suggestion_result += list(product_category.objects.filter(
            Q(product_id__model__istartswith = search_for)).distinct().values_list("product_id__model",flat=True))
        

        #searching for bike type and add to the previous search suggestion
        suggestion_result += list(product_category.objects.filter(
            Q(product_id__bike_type__istartswith = search_for)).distinct().values_list("product_id__bike_type",flat=True))

        # return the json response contain suggestion_result 
        return JsonResponse(suggestion_result,safe=False)
        


# main search
class cyclone_main_search(View):

    def get(self, request):
        search_input = request.GET['search_input']

        # searching through company model gender color and bike type
        search_result = product_category.objects.filter(
            Q(product_id__company__icontains = search_input) | 
            Q(product_id__model__icontains = search_input) | 
            Q(product_id__bike_type__icontains = search_input) | 
            Q(product_id__gender_cat__icontains = search_input) | 
            Q(color__icontains = search_input))
        
        # if the resutl is empty return not found
        if len(search_result) == 0:
            return render(request,'cyclone_category.html')
        
        # search result go through the for loop to fetch need info only from it    
        # creating a list of requred field for response from filtered data
        search_result_items = []
        for item in search_result:
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
            average_star_rating = product_review.objects.filter(category_id = item.id).aggregate(Avg('star_rank'))['star_rank__avg']
            
            # fetching same producs corol variations
            avilable_colors = product_category.objects.filter(product_id = item.product_id).values('color')

            # if there no star rating found we put a defoult value 2 as default
            if average_star_rating is None:
                average_star_rating = 2

            # appdending all the needed info to the cart_items list as a dict
            search_result_items.append({"category_id":category_id, "color":color,"break_type":break_type,"gear_type":gear_type,"mrp":mrp,"seller_price":seller_price,"is_discounted":is_discounted,"model":model,"suspention":suspention,"image":image,"average_star_rating":average_star_rating,"avilable_colors":avilable_colors})
            
        return render(request,'cyclone_category.html',{'cart_items':search_result_items})



# ajx call for different product varient 
class product_varient_selector(View):

    def get(self, request):
        
        """
        when user select diffrent color or frame size of a product'
        it fires an ajax call with product id, selected color and
        selected frame size and this function search for that perticular
        product and send send back with that perticular html part 
        """
        # fetching data from request
        category_id = request.GET['category_id']
        selected_color = request.GET['selected_color']
        selected_frame_size = request.GET['selected_frame_size']

        # product instance to find match product
        # one product_instence can have multiple category in category table
        category_instence = product_category.objects.get(id = category_id)
        product_instence = product.objects.get(product_id = category_instence.product_id.product_id)
    
        # fetch matched product from data base
        mach_product = product_category.objects.filter(product_id = product_instence, color = selected_color, frame_size = selected_frame_size)
        if len(mach_product) == 0:
            mach_product = product_category.objects.filter(product_id = product_instence, frame_size = selected_frame_size)
            
        if len(mach_product) == 0:
            mach_product = product_category.objects.filter(product_id = product_instence, color = selected_color)

        # sliced becouse it filtered 
        mach_product = mach_product[0]

        product_dscpn = product_description.objects.get(product_id = product_instence)
        product_first_pic = product_image.objects.filter(category_id = mach_product).values('product_image')[:1][0]['product_image']
        product_pics = product_image.objects.filter(category_id = mach_product)[1:]
        product_reviews = product_review.objects.filter(category_id = mach_product).values('star_rank','product_comment','review_date','email__first_name')
        average_star_rating = product_review.objects.filter(category_id = mach_product).aggregate(Avg('star_rank'))['star_rank__avg']
        product_color = mach_product.color
        product_frame_size = mach_product.frame_size 

        """
        fetching available color and size of the products also to display
        its id also fetched to uniquely pass the id with it, and it helps 
        to find that item when user click to that veleint 
        """
        # fetching all available colors in this product
        available_colors = product_category.objects.filter(product_id = mach_product.product_id).values('color').exclude(color = product_color).distinct()

        # fetching all available sizes in this product
        available_sizes = product_category.objects.filter(product_id = mach_product.product_id).values('frame_size').exclude(frame_size = product_frame_size).distinct()
        
        # if there no star rating found we put a defoult value 2 as default
        if average_star_rating is None:
            average_star_rating = 2

        product_part_html = render_to_string('product_part.html', {"product_details":mach_product,'product_dscpn':product_dscpn,'product_pics':product_pics,'product_first_pic':product_first_pic,'category_id':category_id,"product_color":product_color,"product_frame_size":product_frame_size,"average_star_rating":int(average_star_rating),"available_colors":available_colors,"available_sizes":available_sizes})
        review_part_html = render_to_string('review_part.html', {"product_details":mach_product,'category_id':category_id,"product_reviews":product_reviews,"average_star_rating":int(average_star_rating)})
        
        return JsonResponse({'status':200,'product_part_html':product_part_html, "review_part_html":review_part_html})



# email subscription
class cyclone_email_subscription(View):

    def post(self, request):

        # fetch data from request
        subscription_email = request.POST['subscription_email']
        
        # cheking if the user email already in data base
        if subscription.objects.filter(email = subscription).exists():
            return JsonResponse({'status':409,'message':'already subscibed'})

        # else register email in database for subscription
        else:
            new_subscriber = subscription(email = subscription_email)
            new_subscriber.save()
            return JsonResponse({'status':200,'message':'email successfully added to the subscription'})
