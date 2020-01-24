from django.contrib import admin
from .models import Product,Contact,Orders,Orderupdate

# Register your models here.
admin.site.register(Product)
admin.site.register(Contact)
admin.site.register(Orders)
admin.site.register(Orderupdate)
