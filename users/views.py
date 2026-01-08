from django.shortcuts import render


def approval_pending(request):
    return render(request, 'users/approval_pending.html')
