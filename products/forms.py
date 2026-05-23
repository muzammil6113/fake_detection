from django import forms
from .models import ProductModel


class ProductModelForm(forms.ModelForm):
    class Meta:
        model   = ProductModel
        fields  = ["name", "brand", "category", "model_code", "description", "image"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class GenerateUnitsForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=500,
                                  label="Number of units to generate")


class TransferForm(forms.Form):
    to_username = forms.CharField(label="Transfer to (username)")
    notes       = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}), required=False)