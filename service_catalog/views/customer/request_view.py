from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect
from django_fsm import can_proceed
from guardian.decorators import permission_required_or_403
from guardian.shortcuts import get_objects_for_user

from service_catalog.filters.request_filter import RequestFilter
from service_catalog.forms.common_forms import RequestMessageForm
from service_catalog.models import Request, Instance, Message


@login_required
def customer_request_list(request):
    f = RequestFilter(request.GET, queryset=get_objects_for_user(request.user, 'service_catalog.view_request'))
    return render(request, 'customer/request/request-list.html', {'filter': f})


@permission_required_or_403('service_catalog.delete_request', (Request, 'id', 'request_id'))
def customer_request_cancel(request, request_id):
    target_request = get_object_or_404(Request, id=request_id)
    if request.method == "POST":
        # check that we can delete the request
        if not can_proceed(target_request.cancel):
            raise PermissionDenied
        target_request.cancel()
        # now delete the request
        target_request.delete()
        return redirect(customer_request_list)
    context = {
        "object": target_request
    }
    return render(request, "customer/request/request-cancel.html", context)


@permission_required_or_403('service_catalog.view_request', (Request, 'id', 'request_id'))
def customer_request_comment(request, request_id):
    target_request = get_object_or_404(Request, id=request_id)
    messages = Message.objects.filter(request=target_request)
    if request.method == "POST":
        form = RequestMessageForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            new_message = form.save()
            new_message.request = target_request
            new_message.sender = request.user
            new_message.save()
            return redirect(customer_request_comment, target_request.id)
    else:
        form = RequestMessageForm()

    context = {
        "form": form,
        "target_request": target_request,
        "messages": messages
    }
    return render(request, "customer/request/request-comment.html", context)
