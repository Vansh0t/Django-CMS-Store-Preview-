

from django.db import models
from django.utils.html import mark_safe
from django.contrib.auth.models import AbstractUser
from django.core.validators import EmailValidator
from easy_thumbnails.files import get_thumbnailer
import cms_site.managers as managers

from .utils.tokens import gen_uuid4_hex
from django.db.transaction import atomic


class Category(models.Model):
    name = models.CharField(max_length=30)
    parameter = models.CharField(max_length=30)
    def __str__(self):
       return self.name
    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
    def save(self, *args, **kwargs):
        from cms_site.managers import CacheManager
        super().save(*args, **kwargs)
        CacheManager.update_categories({self.name: self})

class Filter(models.Model):
    name = models.CharField(max_length=30)
    parameter = models.CharField(max_length=30)
    def __str__(self):
       return self.name
    def save(self, *args, **kwargs):
        from cms_site.managers import CacheManager
        super().save(*args, **kwargs)
        CacheManager.update_filters({self.name: self})

class User(AbstractUser):

    email_vrf_token = models.CharField(max_length=36, null=True, blank = True)
    email_vrf_expiration = models.DateTimeField(null=True, blank = True)

    email_validator = EmailValidator()
    email = models.EmailField(
        'email address',
        unique=True,
        validators=[email_validator],
        error_messages={
            'unique': "A user with such email already exists.",
        }
    )
    email_change = models.EmailField(
        'new email',
        unique=True,
        validators=[email_validator],
        error_messages={
            'unique': "A user with such email already exists.",
        },
        blank=True,
        null=True,
    )

    password_reset_token = models.CharField(max_length=36, null=True, blank = True)
    password_reset_expiration = models.DateTimeField(null=True, blank = True)

    objects = managers.UserManager()

    @property
    def is_verified(self):
        return self.groups.filter(name='verified').exists()
    
    def save(self, *args, **kwargs) -> None:
        customer=None
        if not self.id:
            customer = Customer()
            customer.user = self
        with atomic():
            super().save(*args, **kwargs)
            if customer:
                customer.save()
        


def ware_img_directory_path(instance, filename):
    return f'images/wares/{instance.id}/{gen_uuid4_hex()}-{filename}'

class Ware(models.Model):
    

    title = models.CharField(max_length=30)
    description = models.CharField(max_length=300)
    categories = models.ManyToManyField(Category, blank=True)
    width = models.PositiveSmallIntegerField()
    height = models.PositiveSmallIntegerField()
    quantity = models.PositiveSmallIntegerField(default=1)
    price = models.FloatField(null=False, default=1)
    views = models.PositiveIntegerField(default=0)

    objects = managers.WareManager()
    
    image_main = models.ImageField(upload_to=ware_img_directory_path, default='')
    image_sub1 = models.ImageField(upload_to=ware_img_directory_path, default='', blank=True)
    image_sub2 = models.ImageField(upload_to=ware_img_directory_path, default='', blank=True)
    image_sub3 = models.ImageField(upload_to=ware_img_directory_path, default='', blank=True)
    image_sub4 = models.ImageField(upload_to=ware_img_directory_path, default='', blank=True)
    image_sub5 = models.ImageField(upload_to=ware_img_directory_path, default='', blank=True)
    image_sub6 = models.ImageField(upload_to=ware_img_directory_path, default='', blank=True)
    image_sub7 = models.ImageField(upload_to=ware_img_directory_path, default='', blank=True)
    image_sub8 = models.ImageField(upload_to=ware_img_directory_path, default='', blank=True)

    def __str__(self):
       return self.title
    
    def image_tag(self, image):
        thumb_url = get_thumbnailer(image)['showcase'].url
        return mark_safe('<img style="object-fit:contain;" src="%s" width="100" height="100" />' % thumb_url)
    def image_tag_main(self):
        return self.image_tag(self.image_main)
    def image_tag_sub1(self):
        return self.image_tag(self.image_sub1)
    def image_tag_sub2(self):
        return self.image_tag(self.image_sub2)
    def image_tag_sub3(self):
        return self.image_tag(self.image_sub3)
    def image_tag_sub4(self):
        return self.image_tag(self.image_sub4)
    def image_tag_sub5(self):
        return self.image_tag(self.image_sub5)
    def image_tag_sub6(self):
        return self.image_tag(self.image_sub6)
    def image_tag_sub7(self):
        return self.image_tag(self.image_sub7)
    def image_tag_sub8(self):
        return self.image_tag(self.image_sub8)
    image_tag_main.short_description = 'Image'
    def price_tag(self):
        return f'{self.price}$'
    @property
    def normalized_price(self):
        if self.price.is_integer():
            return int(self.price)
        return self.price
    def get_images(self):
        return self.image_main, \
        self.image_sub1, \
        self.image_sub2, \
        self.image_sub3, \
        self.image_sub4, \
        self.image_sub5, \
        self.image_sub6, \
        self.image_sub7, \
        self.image_sub8
    def _clear_images(self):
        self.image_main = None
        self.image_sub1 = None
        self.image_sub2 = None
        self.image_sub3 = None
        self.image_sub4 = None
        self.image_sub5 = None
        self.image_sub6 = None
        self.image_sub7 = None
        self.image_sub8 = None
    def _restore_images(self, imgs):
        self.image_main = imgs[0]
        self.image_sub1 = imgs[1]
        self.image_sub2 = imgs[2]
        self.image_sub3 = imgs[3]
        self.image_sub4 = imgs[4]
        self.image_sub5 = imgs[5]
        self.image_sub6 = imgs[6]
        self.image_sub7 = imgs[7]
        self.image_sub8 = imgs[8]
    price_tag.short_description = 'Price'
    def save(self, *args, **kwargs):
        #workaround to get id of new instances
        with atomic():
            if not self.id:
                imgs = self.get_images()
                self._clear_images()
                super().save(*args, **kwargs)
                self._restore_images(imgs)
            super().save(*args, **kwargs)



class Customer(models.Model):
    #blank, null are for creation through django admin, consider removing in production
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    
    def __str__(self):
       return self.user.username
    def cart_count_tag(self):
        if self.cart:
            return self.cart.wares.count()
        else:
            return 0
    cart_count_tag.short_description = 'Items in Cart'
    def username_tag(self):
        return self.user.username
    username_tag.short_description = 'Username'



class Cart(models.Model):
    session_id = models.CharField(max_length=40)
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, blank=True, null=True)
    def __str__(self) -> str:
        if self.customer:
            return self.customer.username_tag()
        else:
            #hide most of the session id
            id = self.session_id
            amount = len(id)-4
            return id.replace(id[0:amount], '*'*amount)
    def wares_tag(self):
        return list(self.wares.filter(cart=self))
    wares_tag.short_description="Wares"

class CartWare(models.Model):
    cart = models.ForeignKey(Cart, related_name='wares', on_delete=models.CASCADE)
    ware = models.OneToOneField(Ware, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    def __str__(self) -> str:
        return f'{self.ware.title} ({self.quantity})'


