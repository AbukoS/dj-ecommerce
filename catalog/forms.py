from django import forms
from django_countries.widgets import CountrySelectWidget
from django_countries.fields import CountryField


PAYMENT_CHOICES = (
    ('S', 'Stripe'),
    ('P', 'Paypal'),
)


class AddressForm(forms.Form):
    street_address = forms.CharField()
    apartment_address = forms.CharField()
    country = CountryField(blank_label="Select country").formfield(widget=CountrySelectWidget(attrs={
        "class": "custom-select d-block w-100"
    }))
    zip = forms.CharField(required=False)
    save_info = forms.BooleanField(required=False)
    use_default = forms.BooleanField(required=False)
    payment_option = forms.ChoiceField(
        widget=forms.RadioSelect(), choices=PAYMENT_CHOICES)


class CouponForm(forms.Form):
    code = forms.CharField(widget=forms.TextInput(attrs={
        'class': "form-control",
        'placeholder': "Promo code",
        'aria-label ': "Recipient's username",
        'aria-describedby': "basic-addon2"
    }), max_length=50)
