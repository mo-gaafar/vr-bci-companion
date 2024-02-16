from fastapi import APIRouter, Header, HTTPException, Form, UploadFile, File, Depends, Query, Path, Body
from models.booking import BookingSuccess, BookingCreate, BookingOutPublic
from models.units import UnitBookingOut
from models.customer import CustomerForm, CustomerSignupSuccess
from models.common import PaginationIn, PaginationOut, PaginatedList, SortQuery
from models.users import UserOut, RoleEnum
from typing import Optional
from models.users import UserOut
from util.security import optional_token_header
customer = APIRouter(prefix="/customer", tags=["customer"])


# TODO: POST /customer/register - register customer form and return id (unsecured)
# ~TODO: GET /customer/profile
# ~TODO: PUT /customer/profile/update
# TODO: GET /customer/bookings/ - get all bookings for customer + past or future (default all) + pagination
# TODO: POST /customer/bookings/submit/{unit_id} - submit booking request

# [X] Response Model
# [X] Request Model
# [-] Auth
# [ ] DB
# [ ] Tests
@customer.post("/register", response_model=CustomerSignupSuccess)
async def register_customer(
        customer_form: CustomerForm = Body(..., description="Customer registration form")):
    ''' Customer registration form and return id for use in next step of booking'''
    from repo.customer import create_customer
    return create_customer(customer_form)


# [X] Response Model
# [X] Request Model
# [X] Auth
# [ ] DB
# [ ] Tests


# ! security risk - anyone can get customer booking details if they know the id until we implement auth
@customer.get("/bookings/", response_model=PaginatedList[UnitBookingOut])
async def get_all_bookings(auth_user: Optional[UserOut] = Depends(optional_token_header),
                           customer_id: str = Query(...,
                                                    description="Customer ID"),
                           pagination: PaginationIn = Depends(PaginationIn)):
    ''' Get all bookings for customer + past or future (default all) + pagination'''
    try:
        from repo.booking import get_customer_bookings
        return get_customer_bookings(customer_id, pagination)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# [X] Response Model
# [X] Request Model
# [X] Auth
# [ ] DB
# [ ] Tests


@customer.post("/bookings/create")
async def create_booking(booking_form: BookingCreate = Body(
    ..., description="Booking form"),
        auth_user: Optional[UserOut] = Depends(optional_token_header)):
    ''' Given unit id and customer id (customer should exist first)
    create booking request for customer id or get from bearer (not implemented)'''
    try:
        from repo.booking import create_booking
        booking_indb = create_booking(booking_form)
        return {"detail": "Booking is sent to owner for approval, you will be contacted soon",
                "detail_l1": "تم إرسال الحجز إلى المالك للموافقة \n سيتم الاتصال بك قريبًا",
                "booking": BookingSuccess(**booking_indb.dict(), booking_id=booking_indb.id),
                "success": True}
    except Exception as e:
        if "Unit not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        elif "Customer not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        else:
            return {"detail": str(e).split("\n")[0],
                    # check if split is possible
                    "detail_l1": str(e).split("\n")[1] if len(str(e).split("\n")) > 1 else "حدث خطأ ما",
                    "success": False}
            # raise HTTPException(status_code=400, detail=str(e))
    except:
        raise HTTPException(status_code=500, detail=str(e))
