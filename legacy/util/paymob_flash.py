import paymob
import json

#Setup your secret key
paymob.secret_key = 'egy_sk_test_739f17a09e2c38aa17839cfa4ab66a07b62d1416f0e68fb1a8015ca5f46ad4cf'

#Function returning the intention creation response 
def paymob_payment_intention(order, customer):
    intent = paymob.accept.Intention.create(
        amount=order.total_amount,
        currency="EGP",
        payment_methods=["card","kiosk"],
        items= order.order_contents,
        billing_data={
            "email": customer.email,
            "first_name": customer.name,
            "phone_number": customer.phone,
            "shipping_method": "PKG",
            "country": "EG",
        },
        customer={"first_name": customer.name, "email": customer.email},
        delivery_needed=False,
        extras= {
            "userid": customer.id,
        }
    )

    return intent

# def paymob_confirm_intention
