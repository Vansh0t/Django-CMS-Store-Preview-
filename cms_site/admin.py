from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Ware, Customer, User, Category, Filter, Cart
from post_cms.cms_plugins import CMSWare
from django.db.models import ImageField
from .widgets import ImagePreview

class WareAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'image_tag_main', 'price_tag', 'quantity')
    fields = (  
        'title',
        'description',
        'categories',
        'width',
        'height',
        'quantity',
        'price',
        'views',
        'image_main',
        'image_sub1',
        'image_sub2',
        'image_sub3',
        'image_sub4',
        'image_sub5',
        'image_sub6',
        'image_sub7',
        'image_sub8',

    )
    formfield_overrides = {
        ImageField: {'widget': ImagePreview},
    }

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('username_tag', 'cart_count_tag')
    
class CUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        #('Dev', {'fields': ['password_reset_token']}),
    )
class CartAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ['customer', 'wares_tag']}),
    )
    readonly_fields=['wares_tag']
class FilterAdmin(admin.ModelAdmin):
    list_display = ('name', 'parameter')   
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parameter') 

admin.site.register(User, CUserAdmin)
admin.site.register(Ware, WareAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Filter, FilterAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(CMSWare)