from django import forms


class CheckoutForm(forms.Form):
    email = forms.EmailField()
    full_name = forms.CharField(max_length=160)
    phone = forms.CharField(max_length=40, required=False)
    address_line1 = forms.CharField(max_length=200)
    address_line2 = forms.CharField(max_length=200, required=False)
    city = forms.CharField(max_length=120)
    country = forms.CharField(max_length=120, initial="Kenya")
