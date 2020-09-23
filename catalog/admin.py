from django.contrib import admin
from .models import Item, Order, OrderItem, Address, Payment, Coupon


class ItemAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title', )}
    list_display = [
        'title',
        'price',
        'discount_price'
    ]


class AddressAdmin(admin.ModelAdmin):
    list_display = [
        'street_address',
        'apartment_address',
        'country',
        'zip',
        'default'
    ]


admin.site.register(Item, ItemAdmin)
admin.site.register(Payment)
admin.site.register(Coupon)
admin.site.register(Address, AddressAdmin)
admin.site.register(Order)
admin.site.register(OrderItem)
