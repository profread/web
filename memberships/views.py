from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import authenticate, login
import stripe

from .forms import RegistrationForm
from .models import Member

stripe.api_key = "sk_test_51H10VbJh8KDe9GPFIV2e5f3H7wq21bzdvCB12CznS92vbOavET4ALTsQgNgP0Meb9VSMDuhPc1DhEu4pRw9bs0Sd00iujiazxX"
sand_price_id = "price_1H1ekvJh8KDe9GPF5hhB57QK"
sand_product_id = "prod_HaqRM6XnWLZ6Zi"


# note(cn): You should be able to access this
#           if you are already logged in.
def register(request):
    if not request.method == "POST":
        return render(
            request, "memberships/register.html", {"form": RegistrationForm()}
        )

    form = RegistrationForm(request.POST)
    if not form.is_valid():
        return render(request, "memberships/register.html", {"form": form})

    if not form.cleaned_data["preferred_name"]:
        form.cleaned_data["preferred_name"] = form.cleaned_data["full_name"]

    # todo(cn): error handling
    customer = stripe.Customer.create(
        name=form.cleaned_data["full_name"], email=form.cleaned_data["email"]
    )
    Member.create(
        full_name=form.cleaned_data["full_name"],
        preferred_name=form.cleaned_data["preferred_name"],
        email=form.cleaned_data["email"],
        password=form.cleaned_data["password"],
        birth_date=form.cleaned_data["birth_date"],
        constitution_agreed=form.cleaned_data["constitution_agreed"],
        stripe_customer_id=customer.id,
    )
    # todo(cn): move into Member.create?
    user = authenticate(
        request=request,
        username=form.cleaned_data["email"],
        password=form.cleaned_data["password"],
    )
    if user is None:
        return HttpResponse("failure authenticating")

    login(request, user)

    return HttpResponseRedirect(
        "{}?donation={}".format(
            reverse("payment-setup"), form.cleaned_data["donation_amount"]
        )
    )


def payment_setup(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("register"))

    # todo(cn): handle no donation param
    donation = int(request.GET["donation"])

    member = request.user.member
    session = stripe.checkout.Session.create(
        payment_method_types=["bacs_debit"],
        mode="setup",
        customer=member.stripe_customer_id,
        success_url="{}?donation={}&session_id={{CHECKOUT_SESSION_ID}}".format(
            request.build_absolute_uri(reverse("payment-success")), donation
        ),
        cancel_url=request.build_absolute_uri(reverse("payment-cancel")),
    )

    return render(
        request,
        "memberships/payment-setup.html",
        {
            "session": session,
            "user": request.user,
            "donation": donation,
            "total": donation + 1,
        },
    )


def payment_success(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("register"))

    # todo(cn): handle no donation and session param
    donation = int(request.GET["donation"])
    session_id = request.GET["session_id"]

    session = stripe.checkout.Session.retrieve(id=session_id, expand=["setup_intent"])
    intent = session.setup_intent

    # todo(cn): check if there is even a donation
    donation_price = stripe.Price.create(
        nickname="{} donation".format(donation),
        unit_amount=donation*100,
        currency="gbp",
        recurring={"interval": "year"},
        product=sand_product_id,
    )

    # todo(cn): We probably want to store the subscription id
    #           in the database
    subscription = stripe.Subscription.create(
        customer=intent.customer,
        default_payment_method=intent.payment_method,
        items=[{"price": sand_price_id}, {"price": donation_price.id}],
    )

    return HttpResponse("the payment setup was good.")


def payment_cancel(request):
    pass

