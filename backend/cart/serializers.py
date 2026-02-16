from rest_framework import serializers


class CartItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    product_slug = serializers.CharField()
    quantity = serializers.IntegerField(min_value=0)
    price = serializers.CharField()
    total = serializers.CharField()
    main_image = serializers.CharField(allow_null=True)
    stock = serializers.IntegerField()
    in_stock = serializers.BooleanField()


class CartSerializer(serializers.Serializer):
    items = CartItemSerializer(many=True)
    total = serializers.CharField()
    count = serializers.IntegerField()
    is_authenticated = serializers.BooleanField()


class CartAddSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(required=True, min_value=1, max_value=100)
    override = serializers.BooleanField(required=False, default=False)


class CartUpdateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(required=True, min_value=0, max_value=100)


class CartRemoveSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)

class CartUpdateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(required=True, min_value=0, max_value=100)