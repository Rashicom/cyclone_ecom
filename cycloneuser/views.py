from django.shortcuts import render, redirect
from django.contrib.auth import  authenticate,login, logout
from django.views import View
import random
from django.http.response import JsonResponse
from home.models import CustomUser,product,product_category,product_description,wishlist_items,cart_items,product_image,user_address,user_order,order_list,canceled_orders
from django.core.exceptions import ObjectDoesNotExist
from twilio.rest import Client
from django.conf import settings
from django.db.models import Sum
from django.contrib import messages

# for generating pdf
import io
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from django.http import FileResponse


# Create your views here.

class cyclone_user(View):

    def post(self,request):
        email = request.user
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        contact_number = request.POST['contact_number']
        gender = request.POST['gender']
        CustomUser.objects.filter(email = email).update(first_name = first_name,last_name = last_name, gender = gender, contact_number = contact_number)
        return JsonResponse({'status':'updated'})

    def get(self,request):

        # fetching user info for rendering user profile
        email = request.user.email
        user = CustomUser.objects.get(email = email)
        addresses = user_address.objects.filter(email = user)
        return render(request,'cyclone_myprofile.html',{'user':user,'addresses':addresses})


# user order details
class cyclone_user_order(View):

    def get(self, request):

        # fetching basic info
        email = request.user.email
        user_instencce = CustomUser.objects.get(email = email)
        orders = user_order.objects.filter(email = email).order_by('-order_no')
        order_data = []

        # iteratively appending each order data to order data
        for order in orders:
            """
            from each order we fetching order_no, qty and status
            each order containing many items in it. so from orled list 
            table filtering based on order id and all data append to 
            the order_data table, and same iteratiing for all order
            made by the specific user
            """

            order_no = order.order_no
            order_status = order.order_status
            order_quantity = order_list.objects.filter(order_no = order_no).aggregate(Sum('order_quantity'))['order_quantity__sum']
            order_items = order_list.objects.filter(order_no = order_no).values("category_id__product_id__model","category_id__frame_size","category_id__color","order_quantity","category_id__seller_price")
            order_data.append({"order_no":order_no,"order_status":order_status,"order_quantity":order_quantity,"order_items":order_items})

        return render(request, 'cyclone_user_order.html', {"order_data":order_data})



# order invoice download
class cyclone_order_invoice_download(View):

    def get(self, request, order_no):
        
        # fetch order details
            
        order_quantity = order_list.objects.filter(order_no = order_no).aggregate(Sum('order_quantity'))['order_quantity__sum']
        order_items = order_list.objects.filter(order_no = order_no).values("category_id__product_id__model","category_id__frame_size","category_id__color","order_quantity","category_id__seller_price")
        
        
        
        # pdf creation
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter, bottomup=0)
        
        textobj = pdf.beginText()
        textobj.setTextOrigin(inch,inch)
        
        lines= [
            
            item['category_id__product_id__model'] for item in order_items
                
        ]

        print(lines)
        for line in lines:
            textobj.textLine(line)
        
        pdf.drawText(textobj)
        pdf.showPage()
        pdf.save()
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename="report.pdf")
        


# add new address
class cyclone_addnewaddress(View):

    def post(self,request):
        email = request.user.email
        user = CustomUser.objects.get(email = email)
        address_type = request.POST['address_type']
        place = request.POST['user_place']
        address = request.POST['user_address']
        district = request.POST['user_district']
        state = request.POST['user_state']
        zip_cod = request.POST['user_zip']
        contact_number = request.POST['user_contact_number']
        new_address = user_address(email=user, address_type = address_type, address = address, place = place, district = district, state = state, zip_cod = zip_cod, contact_number = contact_number)
        new_address.save()
        return redirect("user")
    def get(self,request):
        email = request.user.email
        user = CustomUser.objects.get(email = email)
        return render(request,'cyclone_addnewaddress.html',{'user':user})



class cyclone_forgotpassword(View):
    def get(self,request):
        return render(request,'cyclone_forgot_password.html')
    
    def post(self,request):
        email = request.POST['email']
        otp = request.POST['mobile_otp']
        user = CustomUser.objects.get(email = email)
       
        if user.user_otp == otp:
            request.session['email'] = email
            return redirect("userpasswordreset")
        else:
            messages.info(request, "Wrong otp")
            return redirect("forgotpassword")


# otp gerator and send to mobile
class cyclone_mobile_otp_generator(View):
    
    def get(self,request):
        
        # genrating otp and save to data base
        email = request.GET['email']
        otp = random.randint(1000,9999)
        try:
            user = CustomUser.objects.get(email = email)
        except ObjectDoesNotExist:
            return JsonResponse({'status':404, 'message':'invalied email id'})
        user.user_otp = otp
        user.save()

        to_number  = user.contact_number
        if to_number == "":
            return JsonResponse({'status':401,'message':'no registered mobile number'})


        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
                              body='Hello there, your otp is:' + str(otp),
                              from_='+16085915072',
                              to= '+91'+str(to_number)
                          )

        # sendig the otp to the registered contact number
        contact_number = user.contact_number
        print(otp)
         
        return JsonResponse({'status':200, 'message':'otp has been send to your registerd mobile number'})
    


class user_cancel_order(View):

    def post(self,request):
        order_no = request.POST['order_no']
        reason_of_cancel = request.POST['reason_of_cancel']
        payment_return_option = request.POST['payment_return_option']
        order_no_instance = user_order.objects.get(order_no = order_no)

        try:
            new_cancel_order = canceled_orders(order_no = order_no_instance,reason_of_cancel = reason_of_cancel,payment_return_option = payment_return_option)
            new_cancel_order.save()
            update_status = user_order.objects.get(order_no = order_no)
            update_status.order_status = "order canceled"
            update_status.save()
        except Exception:
            return JsonResponse({'status':404, 'message':'cant cancel order'})
        return JsonResponse({'status':200, 'message':'order canceled'})
        

class cyclone_user_password_reset(View):
    
    def get(self, request):

        return render(request, 'cyclone_password_reset.html')

    def post(self, requset):
        """
        password double check compleated in the front end
        so we have to reset the password
        """
        password = requset.POST['password1']
        email = requset.session['email']
        print(password)
        print(email)
        new_password = CustomUser.objects.get(email = email)
        new_password.set_password(str(password))
        new_password.save()
        return redirect("userlogin")
        


def cyclone_deleteaddress(request):
    email = request.user.email
    user = CustomUser.objects.get(email = email)
    address_id = request.POST['address_id']
    user_address.objects.filter(email = user,id = address_id).delete()
    return JsonResponse({'status':'address removed'})

def cyclone_userlogout(request):
    logout(request)
    return redirect("home")
