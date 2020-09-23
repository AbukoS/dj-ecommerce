from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.views.generic import ListView, DetailView, View
from .models import Item, Order, OrderItem, Address, Payment, Coupon
from .forms import AddressForm, CouponForm

import stripe
import json

stripe.api_key = ""


class HomeView(ListView):
    model = Item
    template_name = 'home.html'


class ProductDetail(DetailView):
    model = Item
    template_name = 'product.html'


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'order': order
            }
            return render(self.request, 'order_summary.html', context)
        except ObjectDoesNotExist:
            messages.success(self.request, "You dont have an active order")
            return redirect('home')


class CheckoutView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        # address = Address.objects.get(user=self.request.user, default=True)
        coupon_form = CouponForm()
        form = AddressForm()
        context = {
            'form': form,
            'order': order,
            'coupon_form': coupon_form,
            "DISPLAY_COUPON_FORM": True
            # 'address': address
        }
        return render(self.request, 'checkout.html', context)

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        form = AddressForm(self.request.POST or None)
        if form.is_valid():
            street_address = form.cleaned_data.get('street_address')
            apartment_address = form.cleaned_data.get('apartment_address')
            country = form.cleaned_data.get('country')
            zip = form.cleaned_data.get('zip')
            save_info = form.cleaned_data.get('save_info')
            use_default = form.cleaned_data.get('use_default')
            payment_option = form.cleaned_data.get('payment_option')

            address = Address(
                user=self.request.user,
                street_address=street_address,
                apartment_address=apartment_address,
                country=country,
                zip=zip,
            )
            address.save()
            if save_info:
                address.default = True
                address.save()

            order.address = address
            order.save()

            if use_default:
                address = Address.objects.get(
                    user=self.request.user, default=True)
                order.address = address
                order.save()

            if payment_option == "S":
                return redirect('payment', payment_option="stripe")

            if payment_option == "P":
                return redirect('payment', payment_option="paypal")
            messages.info(self.request, "Invalid payment option")
            return redirect('checkout')
        else:
            print('form invalid')
            return redirect('checkout')


def payment_complete(request):
    body = json.loads(request.body)
    order = Order.objects.get(
        user=request.user, ordered=False, id=body['orderID'])
    payment = Payment(
        user=request.user,
        stripe_charge_id=body['payID'],
        amount=order.get_total()
    )
    payment.save()

    # assign the payment to order
    order.payment = payment
    order.ordered = True
    order.save()
    messages.success(request, "Payment was successful")
    return redirect('home')


class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)

        context = {
            'order': order,
            "DISPLAY_COUPON_FORM": False

        }
        return render(self.request, 'payment.html', context)

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        try:
            customer = stripe.Customer.create(
                email=self.request.user.email,
                description=self.request.user.username,
                source=self.request.POST['stripeToken']
            )
            amount = order.get_total()
            charge = stripe.Charge.create(
                amount=amount * 100,
                currency="usd",
                customer=customer,
                description="Test payment for buteks online",
            )
            payment = Payment(
                user=self.request.user,
                stripe_charge_id=charge['id'],
                amount=amount
            )
            payment.save()

            order.ordered = True
            order.payment = payment
            order.save()

            messages.success(self.request, "Payment was successful")
            return redirect('home')
        except stripe.error.CardError as e:
            messages.info(self.request, f"{e.error.message}")
            return redirect('home')
        except stripe.error.InvalidRequestError as e:
            messages.success(self.request, "Invalid request")
            return redirect('home')
        except stripe.error.AuthenticationError as e:
            messages.success(self.request, "Authentication error")
            return redirect('home')
        except stripe.error.APIConnectionError as e:
            messages.success(self.request, "Check your connection")
            return redirect('home')
        except stripe.error.StripeError as e:
            messages.success(
                self.request, "There was an error please try again")
            return redirect('home')
        except Exception as e:
            messages.success(
                self.request, "A serious error occured we were notified")
            return redirect('home')


class CouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            code = form.cleaned_data.get('code')
            try:
                order = Order.objects.get(user=self.request.user, ordered=False)
                order.coupon = Coupon.objects.get(code=code)
                order.save()
                messages.success(self.request, "Successfully added coupon !")
                return redirect('checkout')
            except ObjectDoesNotExist:
                messages.success(self.request, "You don't have an active order")
                return redirect('home')
        messages.success(self.request, "Enter a valid coupon code")
        return redirect('checkout')



@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False,
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.success(request, f"{item}'s quantity was updated")
            return redirect('order_summary')
        else:
            order.items.add(order_item)
            messages.success(request, f"{item} was added to your cart")
            return redirect('order_summary')

    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered=False, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.success(request, f"{item} was added to your cart")
        return redirect('order_summary')


@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item, user=request.user, ordered=False)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order.items.remove(order_item)
            order.save()
            messages.success(
                request, f"{item.title} was removed from your cart")
            return redirect('order_summary')
        else:
            messages.info(request, f"{item.title} was not in your cart")
            return redirect('order_summary')
    else:
        messages.info(request, "You don't have an active order!")
        return redirect('order_summary')


@login_required
def remove_single_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item, user=request.user, ordered=False)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
                order.save()
            messages.success(request, f"{item}'s quantity was updated")
            return redirect('order_summary')
        else:
            messages.info(request, f"{item.title} was not in your cart")
            return redirect('order_summary')
    else:
        messages.info(request, "You don't have an active order!")
        return redirect('order_summary')
