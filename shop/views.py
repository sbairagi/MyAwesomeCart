from django.shortcuts import render
from django.http import HttpResponse
from .models import Product,Contact,Orders,Orderupdate
from math import ceil
import json
from django.views.decorators.csrf import csrf_exempt
from PayTm import Checksum

MERCHANT_KEY = 'jzi3_hhW1SV34cIo';

# Create your views here.
def index(request):
    # products = Product.objects.all()
    # print(products)
    # n = len(products)
    # nSlides = n//4 + ceil((n/4)-(n//4))

    allProds = []
    catprods = Product.objects.values('category', 'id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prod = Product.objects.filter(category=cat)
        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        allProds.append([prod, range(1, nSlides), nSlides])

    # params = {'no_of_slides':nSlides, 'range': range(1,nSlides),'product': products}
    # allProds = [[products, range(1, nSlides), nSlides],
    #             [products, range(1, nSlides), nSlides]]
    params = {'allProds':allProds}
    return render(request, 'shop/index.html', params)
def searchmatch(query, item):
    '''return  true only if query matches the item'''
    if query in item.desc.lower() or query in item.product_name.lower() or query in item.category.lower():
        return True
    else:
        return False

def search(request):
    query = request.GET.get('search')
    allProds = []
    catprods = Product.objects.values('category', 'id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prodtemp = Product.objects.filter(category=cat)
        prod = [item for item in prodtemp if searchmatch(query, item)]
        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        if len(prod) != 0:
            allProds.append([prod, range(1, nSlides), nSlides])

    # params = {'no_of_slides':nSlides, 'range': range(1,nSlides),'product': products}
    # allProds = [[products, range(1, nSlides), nSlides],
    #             [products, range(1, nSlides), nSlides]]
    params = {'allProds': allProds, "msg":""}
    if len(allProds) == 0 or len(query)<3 :
        params = {'msg': "Please make sure to enter relevent search query"}
    return render(request, 'shop/search.html', params)

def about(request):

    return render(request,'shop/about.html')

def contact(request):
    thank = False
    if request.method == 'POST':
        name = request.POST.get('name','')
        email = request.POST.get('email','')
        phone = request.POST.get('phone','')
        desc = request.POST.get('desc','')
        contact = Contact(name=name,email=email,phone=phone,desc=desc)
        contact.save()
        thank = True
    return render(request,'shop/contact.html',{'thank': thank})

def tracker(request):
    if request.method == 'POST':
        orderid = request.POST.get('orderid','')
        email = request.POST.get('email','')
        try:
            order = Orders.objects.filter(order_id=orderid,email=email)
            if len(order)>0:
                update = Orderupdate.objects.filter(order_id=orderid)
                updates = []
                for item in update:
                    updates.append({'text': item.update_desc,'time': item.timestamp})
                    response = json.dumps([updates, order[0].items_json],default=str)
                return HttpResponse(response)
            else:
                return HttpResponse("{}")
        except Exception as e:
            return HttpResponse('{}')
    return render(request,'shop/tracker.html')



def prodview(request,myid):
    # featch the product using the id
    product = Product.objects.filter(id=myid)
    print(product)

    return render(request,'shop/prodview.html', {'product':product[0]})

def checkout(request):
    if request.method == 'POST':
        items_json = request.POST.get('itemsJson','')
        amount = request.POST.get('amount','')
        name = request.POST.get('name','')
        email = request.POST.get('email','')
        address = request.POST.get('address1' ,'') + " " + request.POST.get('address2','')
        city = request.POST.get('city','')
        state = request.POST.get('state','')
        zip_code = request.POST.get('zip_code','')
        phone = request.POST.get('phone','')
        order = Orders(items_json=items_json,name=name,email=email,address=address,city=city,state=state,zip_code=zip_code,phone=phone, amount=amount)
        order.save()
        update = Orderupdate(order_id=order.order_id,update_desc="the order has been placed")
        update.save()
        thank = True
        id = order.order_id
        # return render(request,'shop/checkout.html', {'thank':thank,'id': id})
        # Request Paytm To Transfer The Amount To Your Account After Payment By User.
        params_dict = {
            'MID':'TTqDiJ35340573365911',
            'ORDER_ID': str(order.order_id),
            'TXN_AMOUNT': str(amount),
            'CUST_ID': email,
            'INDUSTRY_TYPE_ID':'Retail',
            'WEBSITE':'WEBSTAGING',
            'CHANNEL_ID':'WEB',
            'CALLBACK_URL':'http://127.0.0.1:8000/shop/handlerequest/',
        }
        params_dict['CHECKSUMHASH'] = Checksum.generate_checksum(params_dict, MERCHANT_KEY)
        print(params_dict)
        return render(request, 'shop/paytm.html',{'params_dict': params_dict})


    return render(request,'shop/checkout.html')

@csrf_exempt
def handlerequest(request):
    # Paytm Will Sand You a Post Request Here
    form = request.POST
    response_dict = {}
    for i in form.keys():
        response_dict[i] = form[i]
        if i == 'CHECKSUMHASH':
            checksum = form[i]
    verify = Checksum.verify_checksum(response_dict, MERCHANT_KEY, checksum)
    if verify:
        if response_dict['RESPCODE'] == '01':
            print("order Successful")
        else:
            print("order was not successful because" + response_dict['RESPMSG'])
    return render(request, 'shop/paymentstatus.html', {'response': response_dict})