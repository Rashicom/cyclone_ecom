from django.shortcuts import render, redirect
from django.contrib.auth import  authenticate,login, logout
from django.views import View
import random
from django.http.response import JsonResponse
from home.models import CustomUser,product,product_category,product_description,wishlist_items,cart_items,product_image,user_address
from django.core.exceptions import ObjectDoesNotExist
from twilio.rest import Client
from django.conf import settings

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
        otp = request.POST['otp']
        try:
            user = CustomUser.objects.get(email = email)
        except ObjectDoesNotExist:
            return JsonResponse({'status':404, 'message':'invalied email'})
        if user.user_otp == otp:
            return JsonResponse({'status':200,'message':'proceed to password redirect'})
        return JsonResponse({'status':409, 'message':'invalied otp'})



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
        print(contact_number)
         
        return JsonResponse({'status':200, 'message':'otp has been send to your registerd mobile number'})
    def post(self,request):
        pass

def cyclone_deleteaddress(request):
    email = request.user.email
    user = CustomUser.objects.get(email = email)
    address_id = request.POST['address_id']
    user_address.objects.filter(email = user,id = address_id).delete()
    return JsonResponse({'status':'address removed'})

def cyclone_userlogout(request):
    logout(request)
    return redirect("home")
