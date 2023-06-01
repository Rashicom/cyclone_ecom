from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from home.models import CustomUser,product,product_category,user_order,cart_items,product_image,user_address, order_list,guest_cart_items,guest_wishlist_items,discount_coupen,applyed_coupen,applyed_coupen
from django.http.response import JsonResponse
from django.urls import reverse
from django.contrib.sessions.models import Session
import razorpay
from django.conf import settings
import datetime
from django.contrib.auth.mixins import LoginRequiredMixin

# Create your views here.


class cyclone_cart(View):

    def post(self,request):

        # if the quest is try to checkout, after the redirection,
        # we have to bring the user back to car insted of profile page
        if not request.user.is_authenticated:
            request.session['guest_user_cartredirect'] = True
            
        return redirect("checkout")
    
    def get(self,request):
        """
        cart rendered for authenticated user and guest user, if the guest user came
        we check if the user have a session id or not. if not we provide a session id.
        render cart detais id the user have any items in thire carts
        """
        # if guest user
        if not request.user.is_authenticated:
            session_id = request.session.session_key

            # if no session, we create a session to uniqely identify the user
            if session_id is None:
                request.session.create()
            
            # fetch info from guest cart table
            guest_user_instence = Session.objects.get(session_key = request.session.session_key)
            cart = guest_cart_items.objects.filter(session_id = guest_user_instence)
        
        # if authenticated user
        else:
            # fetch info from user cart table
            email = request.user.email
            cart = cart_items.objects.filter(email = email)
        
        
        cart_data = []
        for item in cart:
            product_cat = product_category.objects.get(id = item.category_id.id)
            produc = product.objects.get(product_id = product_cat.product_id.product_id)
            #need to add mutiple images
            image = product_image.objects.filter(category_id = product_cat.id)[:1][0]
            cart_data.append({'company':produc.company,'model':produc.model,'category_id':item.category_id.id,'color':product_cat.color,'frame_size':product_cat.frame_size,'price':product_cat.seller_price ,'mlt_mrp':product_cat.mrp * item.cartitem_quantity,'quantity':product_cat.quantity,'image':image.product_image,'item_qty':item.cartitem_quantity,"mult_price":product_cat.seller_price * item.cartitem_quantity})   
        
        return render(request,'cyclone_cart.html',{'cart_data':cart_data})    



class cyclone_checkout(LoginRequiredMixin,View):
    login_url = "userlogin"


    def post(self,request):
        print("order request hit")

        # fetching data from the request
        email = request.user.email
        user = CustomUser.objects.get(email=email)
        selected_payment = request.POST['selected_payment']

        # if ther is no selected address fetch new adddress
        if not 'selected_address' in request.POST:
            """
            fetch new address fields and save the new addess
            to the database and also deliver item to this address
            """
            address_type = request.POST['address_type']
            user_home_address = request.POST['user_address']
            user_place = request.POST['user_place']
            user_district = request.POST['user_district']
            user_state = request.POST['user_state']
            user_zip = request.POST['user_zip']
            user_contact_number = request.POST['user_contact_number']

            # creating new address in database
            new_address = user_address(email = user, address_type = address_type, address = user_home_address, place = user_place, district = user_district, state = user_state, zip_cod = user_zip, contact_number = user_contact_number)
            new_address.save()

            # setting new address as delivery address
            selected_address = new_address.id
        
        # else there is a address is selected
        else:
            selected_address = request.POST['selected_address']


        coupen_no = request.POST['coupen_no']
        if coupen_no:
            coupen_instence = discount_coupen.objects.get(coupen_no = coupen_no)
            coupen_discount = coupen_instence.discount
        else:
            coupen_instence = None
            coupen_discount = 0 

        # fetching objects corresponding to the request data 
        
        to_address = user_address.objects.get(id = selected_address)
        payment_status = "pending"

        cart_list = cart_items.objects.filter(email = email).values('category_id__seller_price','category_id__mrp', 'category_id', 'cartitem_quantity', 'category_id__product_id__model') 
        mrp_amount = 0
        total_seller_price = 0 

        # calculate this using agragate function
        for item in cart_list:
            total_seller_price += int(item['category_id__seller_price'])
            mrp_amount += int(item['category_id__mrp'])
        seller_discount = mrp_amount - total_seller_price
        
        # checking delivery charge valied or not
        if total_seller_price < 25000:
            delivery_charge = 249
        else:
            delivery_charge = 0

        payment_amount = total_seller_price - coupen_discount + delivery_charge

        # placing order in the order table
        order_status = "checkout not completed"
        new_order = user_order(email = user,payment_method = selected_payment, payment_status = payment_status, order_status = order_status, to_address = to_address, mrp_amount = mrp_amount, seller_discount = seller_discount, coupen_discount = coupen_discount, delivery_charge = delivery_charge, payment_amount = payment_amount)
        new_order.save()

        print("order table updated")

        order_product_list = cart_items.objects.filter(email = email)
        #listing placed orders produsts to order list
        for product in order_product_list:
            new_order_item = order_list(order_no = new_order, category_id = product.category_id, order_quantity = product.cartitem_quantity)
            new_order_item.save()
        
        print("order list table updated")
        # put the used coupen to applayed coupen list to avoide not use in the next order conflict
        if coupen_instence:
            add_coupen = applyed_coupen(email = user,order_no = new_order,coupen_no = coupen_instence)
            add_coupen.save()

        print("coupen table updated")
        order_no = new_order.order_no
        print(order_no)

        # render the order summery page from here
        # becouse we have to pass the order no and order is partially completted
        request.session['order_no'] = order_no
        return redirect("ordersummery")

    def get(self,request):
        email = request.user.email
        user = CustomUser.objects.get(email=email)
        addresses = user_address.objects.filter(email = user)
        cart_list = cart_items.objects.filter(email = email).values('category_id__seller_price','category_id__mrp', 'category_id', 'cartitem_quantity', 'category_id__product_id__model') 
        total_mrp = 0
        total_seller_price = 0 
        for item in cart_list:
            total_seller_price += int(item['category_id__seller_price'])
            total_mrp += int(item['category_id__mrp'])
        discounted = total_mrp - total_seller_price
        
        return render(request,'cyclone_checkout.html',{'user':user,'addresses':addresses, 'cart_list':cart_list,'total_mrp':total_mrp,'discounted':discounted})
        


class quantitycheck(View):
    
    def post(self,request):
        print("quantity check request")
        needed_quantity = request.POST['needed_quantity']
        category_id = request.POST['category_id']
        item = product_category.objects.get(id = category_id)
        if int(item.quantity) < int(needed_quantity):
            return JsonResponse({'status':404,'message':'quantity exceeded'})
        else:

            # for authenticated user
            if request.user.is_authenticated:
                email = request.user.email
                update_qty = cart_items.objects.get(email = email, category_id = category_id)
                update_qty.cartitem_quantity = needed_quantity
                update_qty.save()
                return JsonResponse({'status':200,'message':'quantity available'})
            
            # for quest user
            else:
                session_id = request.session.session_key
                update_guest_qty = guest_cart_items.objects.get(session_id = session_id, category_id = category_id)
                update_guest_qty.cartitem_quantity = needed_quantity
                update_guest_qty.save()
            return JsonResponse({'status':200,'message':'quantity available'})
    


class cyclone_ordersummery(LoginRequiredMixin,View):
    login_url = "userlogin"

    def post(self,request):
        # post request came here after payment done
        # then update order products in to table
        # then change the discription "check out not compleat"
        # "checkout done"
        # order placed message

        email = request.user.email
        user = CustomUser.objects.get(email = email)


        order_items = cart_items.objects.filter(email = user)
        """
        
        print(order_items)
        for item in order_items:
            new_item = order_list(order_no = new_order, category_id = item.category_id)
            new_item.save()
            print("new item updation")
        print("item table updated")
        """
        pass

    def get(self,request):
        
        # fetching_data
        email = request.user.email
        order_no = request.session.get('order_no')

        # fetching data for rendering order summery
        order_price = user_order.objects.get(order_no = order_no)
        seller_price = order_price.mrp_amount - order_price.seller_discount
        saved = order_price.seller_discount + order_price.coupen_discount
        address = user_order.objects.filter(order_no = order_no).values('payment_method','to_address__address_type','to_address__address','to_address__place','to_address__district','to_address__state','to_address__zip_cod','to_address__contact_number','mrp_amount','coupen_discount','delivery_charge','payment_amount')
        cart_list = cart_items.objects.filter(email = email).values('category_id__seller_price','category_id__mrp','category_id__frame_size','category_id__color', 'cartitem_quantity', 'category_id__product_id__model', 'category_id__product_id__company',) 
        discount = order_price.seller_discount + order_price.coupen_discount
        payment_anount = order_price.payment_amount
        

        # if payment methosd is cod render order summory without paymant option 
        order = user_order.objects.get(order_no = order_no)
        if order.payment_method == "Cash on delivery(COD)":
            return render(request,'cyclone_cod_ordersummery.html',{"address_data":address, "cart_list":cart_list,"order_no":order_no,"seller_price":seller_price,"saved":saved,"discount":discount})

        # else continue for summery with paymanet
        # payment initialization
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        DATA = {"amount": payment_anount*100,"currency": "INR","payment_capture":1}
        payment = client.order.create(data=DATA)
        print(payment)
        return render(request,'cyclone_order_summery.html',{"address_data":address, "cart_list":cart_list,"order_no":order_no,"seller_price":seller_price,"saved":saved,"discount":discount,"payment":payment,"key_id":settings.RAZORPAY_KEY_ID})


  
class cyclone_coupen_check(LoginRequiredMixin,View):
    login_url = "userlogin"
    
    # user given coupen no varification
    def post(self,request):
        input_coupen_no = request.POST['input_coupen_no']
        purchase_amount = request.POST['purchase_amount']
        email = request.user.email
        user_instence = CustomUser.objects.get(email = email)
        
        if discount_coupen.objects.filter(coupen_no = input_coupen_no).exists():
            coupen_instence = discount_coupen.objects.get(coupen_no = input_coupen_no)
            type = coupen_instence.coupen_type
            amount = coupen_instence.discount
            if applyed_coupen.objects.filter(email = user_instence, coupen_no = coupen_instence).exists():
                
                if type == "godenpurchase" and purchase_amount > amount:
                    return JsonResponse({'status':200,'message':'coupen valied','amount':amount})
                
                elif type == "Silver purchase" and purchase_amount > amount:
                    return JsonResponse({'status':200,'message':'coupen valied','amount':amount})
                
                else:
                    return JsonResponse({'status':403,'message':'coupen already taken'})
                
            else:
                return JsonResponse({'status':200,'message':'coupen valied','amount':amount})
        else:
            return JsonResponse({'status':404,'message':'invalied coupen'})
        

class cyclone_payment_success(LoginRequiredMixin,View):
    login_url = "userlogin"


    def get(self, request,order_no):
        email = request.user.email
        delivery_date = datetime.datetime.now().date() + datetime.timedelta(days=7)
        order_status = user_order.objects.get(order_no = order_no)
        order_status.payment_status = "payed"
        order_status.order_status = "order placed"
        order_status.save()

        # reducing stock quantity of ordered products
        order_items = order_list.objects.filter(order_no = order_no).values("order_no","order_quantity","category_id")
        
        for item in order_items:
            ordered_product = product_category.objects.get(id = item['category_id'])
            ordered_product.quantity = int(ordered_product.quantity) - int(item['order_quantity'])
            ordered_product.save()
        # clear user cart after order success
        cart_items.objects.filter(email = email).delete()

        return render(request,'cyclone_payment_success.html',{"order_no":order_no,"delivery_date":delivery_date})


# cod sucsess page rendering
class cyclone_cod_success(LoginRequiredMixin,View):
    login_url = "userlogin"

    def get(self, request, order_no):
        return render(request,'cyclone_cod_succuss.html')


# cod order placing
class cyclone_cod_placeorder(LoginRequiredMixin,View):
    login_url = "userlogin"

    def post(self, request):
        email = request.user.email
        order_no = request.POST["order_no"]
        order_status = "order placed"
        new_order = user_order.objects.get(order_no = order_no)
        new_order.order_status = order_status
        new_order.save()

        # reducing stock quantity of ordered products
        order_items = order_list.objects.filter(order_no = order_no).values("order_no","order_quantity","category_id")
        
        for item in order_items:
            ordered_product = product_category.objects.get(id = item['category_id'])
            ordered_product.quantity = int(ordered_product.quantity) - int(item['order_quantity'])
            ordered_product.save()
        # clear user cart after order success
        cart_items.objects.filter(email = email).delete()

        return JsonResponse({'status':200,'message':'order placed'})
        

