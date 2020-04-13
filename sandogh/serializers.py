from . import models
from rest_framework import serializers


class LenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Lender
        fields = '__all__'
