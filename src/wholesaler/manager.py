from django.contrib.auth.base_user import BaseUserManager 
from .models import *

class UserManager(BaseUserManager):

    def create_user(self , email , password = None, **extra_fields):

        if not self.normalize_email(email):
            raise ValueError("Email is required")
        
        # extra_fields['phone_no'] = extra_fields['phone_no']
        user = self.model(email=email , **extra_fields)
        user.set_password(password)
        user.save(using = self.db)
        return user
    

    def create_superuser(self , email , password = None, **extra_fields):
        # USERNAME_FIELD = phone_no
        extra_fields.setdefault('is_staff' , True)
        extra_fields.setdefault('is_superuser' , True)
        extra_fields.setdefault('is_active' , True)

        return self.create_user(email,password, **extra_fields)

class UserMerchentManager(models.Manager):
    def requested(self):
        return self.filter(status=UserMerchent.REQUESTED)

    def confirmed(self):
        return self.filter(status=UserMerchent.CONFIRMED)
    
    def declined(self):
        return self.filter(status=UserMerchent.DECLINED)