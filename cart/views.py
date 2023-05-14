from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from home.models import CustomUser,product,product_category,user_order,cart_items,product_image,user_address, order_list,guest_cart_items,guest_wishlist_items,discount_coupen,applyed_coupen,applyed_coupen
from django.http.response import JsonResponse
from django.urls import reverse
from django.contrib.sessions.models import Session
import razorpay
from django.conf import settings

# Create your views here.


class cyclone_cart(View):

    def post(self,request):

        # need some changes here, we dont want to collect all data from from the front end
        # all is in cart list, just place that list
        category_id_list = request.POST.getlist('category_id[]')
        category_quantity_list = request.POST.getlist('category_quantity[]')
        order_list = []
        for i in range(len(category_id_list)):
            cart_items.objects.filter(category_id = category_id_list[i]).update(cartitem_quantity = category_quantity_list[i])
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
            image = product_image.objects.get(category_id = product_cat.id)
            cart_data.append({'company':produc.company,'model':produc.model,'category_id':item.category_id.id,'color':product_cat.color,'frame_size':product_cat.frame_size,'price':product_cat.seller_price,'mrp':product_cat.mrp,'quantity':product_cat.quantity,'image':image.product_image})   
        
        return render(request,'cyclone_cart.html',{'cart_data':cart_data})    



class cyclone_checkout(View):

    def post(self,request):
        print("order request hit")

        # fetching data from the request
        email = request.user.email
        selected_address = request.POST['selected_address']
        selected_payment = request.POST['selected_payment']
        coupen_no = request.POST['coupen_no']
        
        coupen_instence = discount_coupen.objects.filter(coupen_no = coupen_no).exists()
        if coupen_instence:
            coupen_discount = coupen_instence.discount
        else:
            coupen_discount = 0 

        # fetching objects corresponding to the request data 
        user = CustomUser.objects.get(email=email)
        to_address = user_address.objects.get(id = selected_address)
        payment_status = "pending"

        cart_list = cart_items.objects.filter(email = email).values('category_id__seller_price','category_id__mrp', 'category_id', 'cartitem_quantity', 'category_id__product_id__model') 
        mrp_amount = 0
        total_seller_price = 0 
        for item in cart_list:
            total_seller_price += int(item['category_id__seller_price'])
            mrp_amount += int(item['category_id__mrp'])
        seller_discount = mrp_amount - total_seller_price
        if total_seller_price < 25000:
            delivery_charge = 249
        else:
            delivery_charge = 0
        payment_amount = total_seller_price - coupen_discount + delivery_charge

        # placing order in the order table
        new_order = user_order(email = user,payment_method = selected_payment, payment_status = payment_status, order_status = "checkout not completed", to_address = to_address, mrp_amount = mrp_amount, seller_discount = seller_discount, coupen_discount = coupen_discount, delivery_charge = delivery_charge, payment_amount = payment_amount)
        new_order.save()

        if coupen_instence:
            add_coupen = applyed_coupen(email = user,order_no = new_order,coupen_no = coupen_instence)
            add_coupen.save()

        print("order table updated")
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
            return JsonResponse({'status':'quantity exceeded'})
        else:
            return JsonResponse({'status':'quantity available'})
    
class cyclone_ordersummery(View):
    
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
        
        email = request.user.email
        order_no = request.session.get('order_no')
        order_price = user_order.objects.get(order_no = order_no)
        seller_price = order_price.mrp_amount - order_price.seller_discount
        saved = order_price.seller_discount + order_price.coupen_discount
        address = user_order.objects.filter(order_no = order_no).values('payment_method','to_address__address_type','to_address__address','to_address__place','to_address__district','to_address__state','to_address__zip_cod','to_address__contact_number','mrp_amount','coupen_discount','delivery_charge','payment_amount')
        cart_list = cart_items.objects.filter(email = email).values('category_id__seller_price','category_id__mrp','category_id__frame_size','category_id__color', 'cartitem_quantity', 'category_id__product_id__model', 'category_id__product_id__company',) 


        payment_anount = order_price.payment_amount
        print(payment_anount)
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        DATA = {"amount": payment_anount*100,"currency": "INR","payment_capture":1}
        payment = client.order.create(data=DATA)
        print(payment)
        return render(request,'cyclone_order_summery.html',{"address_data":address, "cart_list":cart_list,"order_no":order_no,"seller_price":seller_price,"saved":saved,"payment":payment,"key_id":settings.RAZORPAY_KEY_ID})
    
class cyclone_coupen_check(View):
    
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
        

class cyclone_payment_success(View):

    def get(self, request):
        return render(request,'cyclone_payment_success.html')