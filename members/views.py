from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime
from django.db import IntegrityError
from django.core.paginator import Paginator
from django.http import HttpResponse
from openpyxl import Workbook
from .models import Member

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('member_list')
        else:
            return render(request, 'members/login.html', {'error': 'Invalid credentials'})
    return render(request, 'members/login.html')

@login_required
def member_list(request):
    # Update active status for expired memberships
    from django.utils import timezone
    today = timezone.now().date()
    Member.objects.filter(membership_end_date__lt=today, is_active=True).update(is_active=False)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            name = request.POST.get('name')
            email = request.POST.get('email')
            phone_number = request.POST.get('phone_number')
            dob_str = request.POST.get('dob')
            gender = request.POST.get('gender')
            join_date_str = request.POST.get('join_date')
            membership_type = request.POST.get('membership_type')
            membership_start_date = request.POST.get('membership_start_date')
            membership_end_date = request.POST.get('membership_end_date')
            is_active = request.POST.get('is_active') == 'on'
            if not email.endswith('@gmail.com'):
                messages.error(request, 'Please enter valid email address.')
                return redirect('member_list')
            try:
                join_date = datetime.strptime(join_date_str, '%Y-%m-%d').date()
                if join_date > timezone.now().date():
                    messages.error(request, 'Join date cannot be in the future.')
                    return redirect('member_list')
            except ValueError:
                messages.error(request, 'Invalid join date format.')
                return redirect('member_list')
            dob = None
            if dob_str:
                try:
                    dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
                except ValueError:
                    messages.error(request, 'Invalid DOB format.')
                    return redirect('member_list')
            try:
                Member.objects.create(
                    name=name, email=email, phone_number=phone_number, dob=dob, gender=gender, join_date=join_date, membership_type=membership_type,
                    membership_start_date=membership_start_date, membership_end_date=membership_end_date, is_active=is_active
                )
            except IntegrityError:
                messages.error(request, 'A member with this email already exists.')
                return redirect('member_list')
        elif action == 'update':
            member_id = request.POST.get('member_id')
            member = Member.objects.get(id=member_id)
            member.name = request.POST.get('name')
            email = request.POST.get('email')
            if not email.endswith('@gmail.com'):
                messages.error(request, 'Please enter valid email address.')
                return redirect('member_list')
            member.email = email
            member.phone_number = request.POST.get('phone_number')
            dob_str = request.POST.get('dob')
            dob = None
            if dob_str:
                try:
                    dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
                except ValueError:
                    messages.error(request, 'Invalid DOB format.')
                    return redirect('member_list')
            member.dob = dob
            join_date_str = request.POST.get('join_date')
            try:
                join_date = datetime.strptime(join_date_str, '%Y-%m-%d').date()
                if join_date > timezone.now().date():
                    messages.error(request, 'Join date cannot be in the future.')
                    return redirect('member_list')
            except ValueError:
                messages.error(request, 'Invalid join date format.')
                return redirect('member_list')
            member.join_date = join_date
            member.membership_type = request.POST.get('membership_type')
            member.membership_start_date = request.POST.get('membership_start_date')
            member.membership_end_date = request.POST.get('membership_end_date')
            member.gender = request.POST.get('gender')
            member.is_active = request.POST.get('is_active') == 'on'
            member.save()
        elif action == 'delete':
            member_id = request.POST.get('member_id')
            Member.objects.filter(id=member_id).delete()
        return redirect('member_list')
    search_query = request.GET.get('search', '')
    if search_query:
        members = Member.objects.filter(
            Q(name__icontains=search_query) | Q(email__icontains=search_query)
        ).order_by('id')
    else:
        members = Member.objects.all().order_by('id')
    total_members = Member.objects.count()
    active_members = Member.objects.filter(is_active=True).count()
    inactive_members = total_members - active_members
    membership_types = Member.objects.values('membership_type').annotate(count=Count('membership_type')).order_by('-count')
    paginator = Paginator(members, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'members': page_obj,
        'search_query': search_query,
        'total_members': total_members,
        'active_members': active_members,
        'inactive_members': inactive_members,
        'membership_types': membership_types,
    }
    return render(request, 'members/member_list.html', context)

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def export_excel(request):
    members = Member.objects.all()
    wb = Workbook()
    ws = wb.active
    ws.title = "Members"

    # Add headers
    headers = ['Name', 'Email', 'Phone Number', 'Date of Birth', 'Gender', 'Join Date', 'Membership Type', 'Membership Start Date', 'Membership End Date', 'Is Active']
    for col_num, header in enumerate(headers, 1):
        ws.cell(row=1, column=col_num, value=header)

    # Add data
    for row_num, member in enumerate(members, 2):
        ws.cell(row=row_num, column=1, value=member.name)
        ws.cell(row=row_num, column=2, value=member.email)
        ws.cell(row=row_num, column=3, value=member.phone_number)
        ws.cell(row=row_num, column=4, value=member.dob.strftime('%Y-%m-%d') if member.dob else '')
        ws.cell(row=row_num, column=5, value=member.gender)
        ws.cell(row=row_num, column=6, value=member.join_date.strftime('%Y-%m-%d'))
        ws.cell(row=row_num, column=7, value=member.membership_type)
        ws.cell(row=row_num, column=8, value=member.membership_start_date.strftime('%Y-%m-%d'))
        ws.cell(row=row_num, column=9, value=member.membership_end_date.strftime('%Y-%m-%d'))
        ws.cell(row=row_num, column=10, value='Yes' if member.is_active else 'No')

    # Create response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=members.xlsx'
    wb.save(response)
    return response

def add_member(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        dob_str = request.POST.get('dob')
        gender = request.POST.get('gender')
        join_date_str = request.POST.get('join_date')
        membership_type = request.POST.get('membership_type')
        membership_start_date = request.POST.get('membership_start_date')
        membership_end_date = request.POST.get('membership_end_date')
        is_active = request.POST.get('is_active') == 'on'
        if not email.endswith('@gmail.com'):
            return render(request, 'members/add_member.html', {'error': 'Please enter valid email address.'})
        try:
            join_date = datetime.strptime(join_date_str, '%Y-%m-%d').date()
            if join_date > timezone.now().date():
                return render(request, 'members/add_member.html', {'error': 'Join date cannot be in the future.'})
        except ValueError:
            return render(request, 'members/add_member.html', {'error': 'Invalid join date format.'})
        dob = None
        if dob_str:
            try:
                dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                return render(request, 'members/add_member.html', {'error': 'Invalid DOB format.'})
        try:
            Member.objects.create(
                name=name, email=email, phone_number=phone_number, dob=dob, gender=gender, join_date=join_date, membership_type=membership_type,
                membership_start_date=membership_start_date, membership_end_date=membership_end_date, is_active=is_active
            )
        except IntegrityError:
            return render(request, 'members/add_member.html', {'error': 'A member with this email already exists.'})
        return redirect('member_list')
    return render(request, 'members/add_member.html')
