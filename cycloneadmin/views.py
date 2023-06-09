from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from home.models import CustomUser,product,product_category,product_description,product_image,user_order,discount_coupen,order_list
from django.views import View
from django.http.response import JsonResponse
from django.core import serializers
from datetime import date, timedelta
from django.db.models import Sum, Count
import json
from django.http import FileResponse, HttpResponse

# for pdf generation
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
import io
import csv

from django.contrib.auth.decorators import user_passes_test

# Create your views here.


def cycloneadmin_login(request):

    # check if the user is already logedin
    if request.user.is_authenticated:
        return redirect("dashboard")

    # if the request is post fetch data
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]
        user = authenticate(email = email,password = password)
        
        # check the user is a valied admin
        if user is not None and user.is_superuser:
            login(request,user)
            return redirect("dashboard")
        else:
            messages.info(request,"Admin user not found or incorrect password")
    # if method is get
    return render(request,'cycloneadmin_login.html')

def cycloneadmin_logout(request):
    logout(request)
    return redirect("login")



class cycloneadmin_dashboard(View):


    def get(self,request):
        user_count = CustomUser.objects.filter(is_superuser = False).count()   
        sales_today = user_order.objects.filter(order_date = date.today()).count()
        total_shipment = user_order.objects.count()
        total_revenue = user_order.objects.all().aggregate(Sum("payment_amount"))['payment_amount__sum']
        category_sales = order_list.objects.values('category_id__product_id__bike_type').annotate(Count('category_id__product_id__bike_type'))
        day_sale = order_list.objects.values('order_no__order_date').annotate(item_sum = Sum('order_quantity'))
        total_revenue_status = user_order.objects.values('order_date').annotate(date_total_revenue = Sum('payment_amount'))

        dashboard_data = {"user_count":user_count,"sales_today":sales_today,"total_shipment":total_shipment,"total_revenue":total_revenue,"category_sales":category_sales,"day_sale":day_sale,"total_revenue_status":total_revenue_status}
        
        
        return render(request,'cycloneadmin_dashboard.html',dashboard_data)



# user information 
def cycloneadmin_userinfo(request):
    return render(request,'cycloneadmin_userinfo.html',{"data":CustomUser.objects.filter(is_superuser=False)})


# unbload or bloak user
class cycloneadmin_edituseracces(View):

    def post(self,request):
        email = request.POST['email']
        user = CustomUser.objects.get(email = email)
        if user.is_active:
            user.is_active = False
        else:
            user.is_active = True
        user.save()
        return JsonResponse({'status':'200','message':user.is_active})


def cycloneadmin_sellerinfo(request):
    return render(request,'cycloneadmin_sellerinfo.html')


# products view
def cycloneadmin_products(request):
    
    # fetching info from data base
    products = product.objects.values("product_id","company","model","bike_type")

    return render(request,'cycloneadmin_products.html',{"products":products})


def cycloneadmin_category(request):
    # fetching data from database to  list out categories
    # product and product_catogories are joined to fetch the data
    
    categories = product_category.objects.values("product_id__company","product_id__model","frame_size","break_type","color","is_discontinued","quantity","id")
    
    return render(request,'cycloneadmin_category.html',{"categories":categories})



def cycloneadmin_addcategory(request):
    
    if request.method == "POST":

        product_imgs = request.FILES.getlist('product_imgs[]')
        
        
        # find the record using this info
        company = request.POST['company']
        model = request.POST['model']

        # update record
        frame_size = request.POST['frame_size']
        color = request.POST['color']
        break_type = request.POST['break_type']
        gear_type = request.POST['gear_type']
        mrp = request.POST['mrp']
        seller_price = request.POST['seller_price']
        quantity = request.POST['quantity']
        is_discounted = request.POST['is_discounted']
        
        
        # update all the information , not a good practce
        # only update changed fields using ajax
        try:    
            product_id = product.objects.get(model = model, company = company)
            new_category = product_category(product_id = product_id,frame_size = frame_size,color = color, break_type = break_type, gear_type = gear_type, mrp = mrp ,seller_price = seller_price, quantity = quantity, is_discounted = is_discounted)      
            new_category.save()  

            # iteratively update all pictures in data base from picture list
            for image in product_imgs:
                new_image = product_image(category_id = new_category, product_image = image)  
                new_image.save()
            
        except product.DoesNotExist:
            messages.info(request,"such product does not exist")
            return redirect("addcategory")
       
        messages.info(request,"new category successfully added")   
        return redirect("addcategory")

    products = product.objects.values('company','model')
    return render(request,'cycloneadmin_addcategory.html',{'products':products})



class cycloneadmin_editcategory(View):

    def get(self,request,category_id):

        productcat = product_category.objects.get(id = category_id)
        print(productcat.is_discounted)
        return render(request,'cycloneadmin_editcategory.html',{"productcat":productcat})

    def post(self,request,category_id):
        
        # fetch pictures from the backend
        current_imgs = request.FILES.getlist('current_imgs[]')
        
        # fetch other fields
        frame_size = request.POST['frame_size']
        color = request.POST['color']
        break_type = request.POST['break_type']
        gear_type = request.POST['gear_type']
        mrp = request.POST['mrp']
        seller_price = request.POST['seller_price']
        quantity = request.POST['quantity']
        is_discounted = request.POST['is_discounted']

        
        # update all the information , not a good practce
        # only update changed fields using ajax
        try:
            update_product = product_category.objects.get(id = category_id)    
            
            update_product.frame_size = frame_size
            update_product.color = color
            update_product.break_type = break_type
            update_product.gear_type = gear_type
            update_product.mrp = mrp
            update_product.seller_price = seller_price
            update_product.quantity = quantity
            update_product.is_discounted = is_discounted
            
            update_product.save()
            # iteratively update all pictures in data base from picture list
            for image in current_imgs:
                new_image = product_image(category_id = update_product, product_image = image)  
                new_image.save()        
            messages.info(request,"product updated successfully")
        except Exception as e:
            print(e)
            messages.info(request,"such product does not exist")
            return redirect("addcategory") 
        
        return redirect("category")


# product continue / discontinue
class cycloneadmin_delete_category(View):

    def get(self, request):
        
        category_id = request.GET['category_id']

        # fetch product object
        discontinue_product = product_category.objects.get(id = category_id)
        
        # if product is available set to true / discontinue
        if discontinue_product.is_discontinued == False:
            discontinue_product.is_discontinued = True
            discontinue_product.save()
            return JsonResponse({'status':200,'message':'category discontinued'})
        # else set to false / continue
        else:
            discontinue_product.is_discontinued = False
            discontinue_product.save()
            return JsonResponse({'status':200,'message':'category back to available'})



def cycloneadmin_orders(request):

    orders = user_order.objects.values('order_no','email','order_date','payment_status','order_status')
    return render(request,'cycloneadmin_orders.html',{'orders':orders})



def cycloneadmin_reports(request):
    return render(request,'cycloneadmin_reports.html')



class cycloneadmin_addproduct(View):

    def get(self, request):
        return render(request,'cycloneadmin_addproduct.html')

    def post(self, request):

        # fetch data if the request is post
        if request.method == "POST":

            # for product table
            company = request.POST['company']
            model = request.POST['model']
            wheel_size = request.POST['wheel_size']
            suspention = request.POST['suspention']
            internal_cabling = request.POST['internal_cabling']
            bike_type = request.POST['bike_type']
            gender_cat = request.POST['gender_cat']

            # for product_description table
            terrain_description = request.POST['terrain_description']
            strength_description = request.POST['strength_description']
            perfomance_description = request.POST['perfomance_description']
            precision_description = request.POST['precision_description']
            
            # checking the product is already exist or not
            if product.objects.filter(company = company, model = model).exists():
                messages.warning(request,"Product already exist")
                return redirect("addproduct")


            newproduct = product(company = company, model = model, wheel_size = wheel_size, suspention = suspention, internal_cabling = internal_cabling, bike_type = bike_type, gender_cat = gender_cat)
            newproduct.save()
            newdescription = product_description(product_id = newproduct, terrain_description = terrain_description, strength_description = strength_description, perfomance_description = perfomance_description, precision_description = precision_description)
            newdescription.save()

            messages.info(request,"New Product added successfully")
            return redirect("addproduct")        




def cycloneadmin_editproduct(request,product_id):

    if request.method == 'POST':
        
        # fetch the info from user edit request
        company = request.POST['company']
        model = request.POST['model']
        wheel_size = request.POST['wheel_size']
        suspention = request.POST['suspention']
        internal_cabling = request.POST['internal_cabling']
        bike_type = request.POST['bike_type']
        gender_cat = request.POST['gender_cat']
        terrain_description = request.POST['terrain_description']
        strength_description = request.POST['strength_description']
        perfomance_description = request.POST['perfomance_description']
        precision_description = request.POST['precision_description']
        
        # update all the information , not a good practce
        # only update changed fields only using ajax
        product.objects.filter(product_id = product_id).update(company = company, model = model, wheel_size = wheel_size, suspention = suspention, internal_cabling = internal_cabling, bike_type = bike_type, gender_cat = gender_cat)
        product_description.objects.filter(product_id = product_id).update(terrain_description = terrain_description, strength_description = strength_description, perfomance_description = perfomance_description, precision_description = precision_description)
        print("data updated")
        return redirect("products")

    # using product is fetch data and pass to the html to edit
    products = product.objects.select_related("product_id").values("company","model","wheel_size","suspention","internal_cabling","bike_type","gender_cat","product_description__terrain_description","product_description__strength_description","product_description__perfomance_description","product_description__precision_description").get(product_id = product_id)
    return render(request,'cycloneadmin_editproduct.html',{"products":products})

class cycloneadmin_coupenmanagemant(View):

    def get(self, request):
        coupens = discount_coupen.objects.values("coupen_no","coupen_type","discount","expiry_date")
        return render(request,'cycloneadmin_coupen_managemant.html',{'coupens':coupens})



class cycloneadmin_offer_management(View):
    
    def get(self, request):

        offer_list = product_category.objects.filter(is_discounted = True).values('product_id__company','product_id__model','mrp','seller_price')
    
        return render(request, 'cycloneadmin_offer_management.html',{"offer_list":offer_list})


class cycloneadmin_add_offer(View):

    def post(self, request):
        """
        if the offer model is none it means we have to put offer
        to the all models in that product. else that specific products only
        """

        offer_company = request.POST['offer_company']
        offer_model = request.POST['offer_model']
        offer_price = request.POST['offer_price']
        print('request hit')
        # if offer for specific products
        if offer_model:

            new_offer_item = product_category.objects.filter(product_id__company = offer_company, product_id__model = offer_model)
            # if the product not found
            if len(new_offer_item ) == 0 :
                return JsonResponse({'status':404,'message':'product not found'})

            
            return JsonResponse({'status':200,'message':'products added to offer category'})
        
        # offer for all model in the product
        else:
            pass


        


class cyclone_addcoupen(View):
    
    # admin coupen add request
    def post(self, request):
        print("add coupen request")

        # fetching coupen data from ajax post request
        coupen_no = request.POST['coupen_no']
        coupen_type = request.POST['coupen_type']
        coupen_discount = request.POST['coupen_discount']
        coupen_expiry_date = request.POST['coupen_expiry_date']

        # checking the coupen already exixt or not
        if discount_coupen.objects.filter(coupen_no = coupen_no).exists():
            return JsonResponse({'status':409, 'message':'coupen already exist'})    

        # updating data base
        new_coupen = discount_coupen(coupen_no = coupen_no,coupen_type = coupen_type,discount = coupen_discount, expiry_date = coupen_expiry_date)
        new_coupen.save()

        return JsonResponse({'status':200, 'message':'coupen updated'})


# delete coupen
class cycloneadmin_deletecoupen(View):
    
    def post(self, request):
        coupen_no = request.POST['coupen_no']
        discount_coupen.objects.get(coupen_no = coupen_no).delete()
        return JsonResponse({'status':200,'message':'coupen removed successfully'})



# dicontinue or continue product/ all categories

class cycloneadmin_discontinuproduct(View):

    def get(self,request):
        print('didcontinue hit')
        """
        when a product need to be discontinued we have to set is_discontinue
        filds of every category of the pericular product as True
        """

        product_id = request.GET['product_id']
        product_dis_continue = product.objects.get(product_id = product_id)
        product_category.objects.filter(product_id = product_dis_continue).update(is_discontinued = True)
        return JsonResponse({'status':200,'message':'product discontinued'})


class cycloneadmin_order_updation(View):

    def get(self, request):
        order_no = request.GET['order_no']
        order = user_order.objects.get(order_no = order_no)
        
        return JsonResponse({"status":200,"order_no":order.order_no,"payment_method":order.payment_method,"payment_status":order.payment_status,"order_status":order.order_status,'email':order.email.email,'order_date':order.order_date})


    def post(self, request):
        order_no = request.POST['order_no']
        update_val = request.POST['update_val']
        print(update_val)
        try:
            user_order.objects.filter(order_no = order_no).update(order_status = update_val)
        except Exception:
            return JsonResponse({'status':404,'message':'updation filed'})
        return JsonResponse({'status':200,'message':'status updaed'})

class cycloneadmin_cancel_order(View):

    def post(self, request):
        order_no = request.POST['order_no']
        try:
            user_order.objects.filter(order_no = order_no).update(order_status = "cancelled by admin")
        except Exception:
            return JsonResponse({'status':404, 'messages':'cancelation filed'})

        return JsonResponse({'status':200, 'messages':'order cancelled'})


class cycloneadmin_report_generator(View):
    
    def get(self,request):

        # this returning sales report to admin
        from_date = request.GET['from_date']
        to_date = request.GET['to_date']

        total_shipments = user_order.objects.filter(order_date__gte = from_date , order_date__lte = to_date).count()
        total_business = user_order.objects.filter(order_date__gte = from_date , order_date__lte = to_date).aggregate(Sum('payment_amount'))['payment_amount__sum']
        total_cod_order = user_order.objects.filter(order_date__gte = from_date , order_date__lte = to_date,payment_method = "Cash on delivery(COD)").count()
        total_payed_orders = user_order.objects.filter(order_date__gte = from_date , order_date__lte = to_date,payment_method = "Net banking / UPI").count()
        canceled_orders = user_order.objects.filter(order_date__gte = from_date , order_date__lte = to_date,order_status = "order canceled").count()
        total_users = CustomUser.objects.count() - 1
        total_product_quantity = product_category.objects.aggregate(Sum("quantity"))['quantity__sum']
        
        report = {"total_shipments":total_shipments,"total_business":total_business,"total_cod_order":total_cod_order,"total_payed_orders":total_payed_orders,"canceled_orders":canceled_orders,"total_users":total_users,"total_product_quantity":total_product_quantity}
        return JsonResponse({'status':200,"report":report})


class pdf_report_downloader(View):

    def get(self, request):

        # fetching data from the url
        from_date = request.GET['from_date']
        to_date = request.GET['to_date']

        # fetching data from data base by filtering with the date range
        total_shipments = user_order.objects.filter(order_date__gte = from_date , order_date__lte = to_date).count()
        total_business = user_order.objects.filter(order_date__gte = from_date , order_date__lte = to_date).aggregate(Sum('payment_amount'))['payment_amount__sum']
        total_cod_order = user_order.objects.filter(order_date__gte = from_date , order_date__lte = to_date,payment_method = "Cash on delivery(COD)").count()
        total_payed_orders = user_order.objects.filter(order_date__gte = from_date , order_date__lte = to_date,payment_method = "Net banking / UPI").count()
        canceled_orders = user_order.objects.filter(order_date__gte = from_date , order_date__lte = to_date,order_status = "order canceled").count()
        total_users = CustomUser.objects.count() - 1
        total_product_quantity = product_category.objects.aggregate(Sum("quantity"))['quantity__sum']
        
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter, bottomup=0)
        
        textobj = pdf.beginText()
        textobj.setTextOrigin(inch,inch)
        
        lines= [
            "total shipments :"+str(total_shipments),
            "total business :"+str(total_business),
            "total cod order :"+str(total_cod_order),
            "total payed orders :"+str(total_payed_orders),
            "canceled orders :"+str(canceled_orders),
            "total users :"+str(total_users),
            "total product quantity :"+str(total_product_quantity)
        ]

        for line in lines:
            textobj.textLine(line)
        
        pdf.drawText(textobj)
        pdf.showPage()
        pdf.save()
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename="report.pdf")

 
class csv_report_downloader(View):
    
    def get(self, request):
               
        # fetching data from the url
        from_date = request.GET['from_date']
        to_date = request.GET['to_date']

        # fetching data from data base by filtering with the date range
        total_shipments = user_order.objects.filter(order_date__gte = from_date , order_date__lte = to_date).count()
        total_business = user_order.objects.filter(order_date__gte = from_date , order_date__lte = to_date).aggregate(Sum('payment_amount'))['payment_amount__sum']
        total_cod_order = user_order.objects.filter(order_date__gte = from_date , order_date__lte = to_date,payment_method = "Cash on delivery(COD)").count()
        total_payed_orders = user_order.objects.filter(order_date__gte = from_date , order_date__lte = to_date,payment_method = "Net banking / UPI").count()
        canceled_orders = user_order.objects.filter(order_date__gte = from_date , order_date__lte = to_date,order_status = "order canceled").count()
        total_users = CustomUser.objects.count() - 1
        total_product_quantity = product_category.objects.aggregate(Sum("quantity"))['quantity__sum']
        
        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="report.csv"'},
        )

        # write contents to the csv file
        writer = csv.writer(response)
        writer.writerow(["total_shipments",total_shipments])
        writer.writerow(["total_business",total_business])
        writer.writerow(["total_cod_order",total_cod_order])
        writer.writerow(["total_payed_orders",total_payed_orders])
        writer.writerow(["canceled_orders",canceled_orders])
        writer.writerow(["total_users",total_users])
        writer.writerow(["total_product_quantity",total_product_quantity])

        return response

    

