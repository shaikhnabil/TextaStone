from django.contrib import admin
from src.wholesaler import models

class user_fields(admin.ModelAdmin):
    user_field = ['phone_no','email','address']

admin.site.register(models.CustomUser,user_fields)
admin.site.register(models.UserMerchent)
admin.site.register(models.Saree)
admin.site.register(models.SareeDatePrice)
admin.site.register(models.DistributorRecord)
# admin.site.register(models.UserType)


# admin.site.register(models.WholesalerSaree)
# admin.site.register(models.RetailerSaree)
# admin.site.register(models.CustomerRecords)

# Register your models here.
