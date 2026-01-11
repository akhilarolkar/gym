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
from openpyxl import Workbook, load_workbook
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
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
    sort_by = request.GET.get('sort_by', 'join_date')
    direction = request.GET.get('direction', 'desc')

    # Validate sort_by field
    allowed_sort_fields = ['id', 'name', 'email', 'join_date', 'membership_type', 'is_active']
    if sort_by not in allowed_sort_fields:
        sort_by = 'id'

    # Validate direction
    if direction not in ['asc', 'desc']:
        direction = 'asc'

    # Build order_by string
    order_by_field = f'-{sort_by}' if direction == 'desc' else sort_by

    if search_query:
        members = Member.objects.filter(
            Q(name__icontains=search_query) | Q(email__icontains=search_query)
        ).order_by(order_by_field)
    else:
        members = Member.objects.all().order_by(order_by_field)
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
        'sort_by': sort_by,
        'direction': direction,
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

@login_required
def import_excel(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        try:
            wb = load_workbook(excel_file)
            ws = wb.active
            imported_count = 0
            errors = []
            for row in ws.iter_rows(min_row=2, values_only=True):  # Skip header
                if len(row) < 10:
                    errors.append("Row has insufficient columns")
                    continue
                name, email, phone_number, dob_str, gender, join_date_str, membership_type, membership_start_date_str, membership_end_date_str, is_active_str = row[:10]
                if not name or not email:
                    errors.append(f"Name and email are required for row: {row}")
                    continue
                if not email.endswith('@gmail.com'):
                    errors.append(f"Invalid email for {name}: {email}")
                    continue
                try:
                    join_date = datetime.strptime(join_date_str, '%Y-%m-%d').date()
                    if join_date > timezone.now().date():
                        errors.append(f"Join date cannot be in the future for {name}")
                        continue
                except (ValueError, TypeError):
                    errors.append(f"Invalid join date format for {name}: {join_date_str}")
                    continue
                dob = None
                if dob_str:
                    try:
                        dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        errors.append(f"Invalid DOB format for {name}: {dob_str}")
                        continue
                try:
                    membership_start_date = datetime.strptime(membership_start_date_str, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    errors.append(f"Invalid membership start date format for {name}: {membership_start_date_str}")
                    continue
                try:
                    membership_end_date = datetime.strptime(membership_end_date_str, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    errors.append(f"Invalid membership end date format for {name}: {membership_end_date_str}")
                    continue
                is_active = is_active_str.lower() == 'yes' if is_active_str else False
                try:
                    Member.objects.create(
                        name=name, email=email, phone_number=phone_number or '', dob=dob, gender=gender or '',
                        join_date=join_date, membership_type=membership_type,
                        membership_start_date=membership_start_date, membership_end_date=membership_end_date,
                        is_active=is_active
                    )
                    imported_count += 1
                except IntegrityError:
                    errors.append(f"Member with email {email} already exists")
                    continue
                except Exception as e:
                    errors.append(f"Error creating member {name}: {str(e)}")
                    continue
            if imported_count > 0:
                messages.success(request, f"Successfully imported {imported_count} members.")
            if errors:
                for error in errors:
                    messages.error(request, error)
        except Exception as e:
            messages.error(request, f"Error processing file: {str(e)}")
    return redirect('member_list')

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

@login_required
def generate_invoice_pdf(request, member_id):
    try:
        member = Member.objects.get(id=member_id)
    except Member.DoesNotExist:
        messages.error(request, 'Member not found.')
        return redirect('member_list')

    # Define membership pricing
    membership_prices = {
        'strength': 50.00,
        'cardio': 40.00,
        'crossfit': 60.00,
    }

    # Calculate charges
    price_per_month = membership_prices.get(member.membership_type.lower(), 50.00)
    duration_days = (member.membership_end_date - member.membership_start_date).days
    duration_months = max(1, round(duration_days / 30))  # Approximate months
    total_amount = price_per_month * duration_months

    # Create PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{member.id}_{timezone.now().date()}.pdf"'

    # Create PDF document
    doc = SimpleDocTemplate(response, pagesize=letter)
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1  # Center
    )
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=20
    )
    normal_style = styles['Normal']

    # Build PDF content
    content = []

    # Title
    content.append(Paragraph("Gym Membership Invoice", title_style))
    content.append(Spacer(1, 12))

    # Invoice details
    invoice_number = f"INV-{member.id}-{timezone.now().strftime('%Y%m%d')}"
    invoice_date = timezone.now().strftime('%B %d, %Y')

    content.append(Paragraph(f"<b>Invoice Number:</b> {invoice_number}", normal_style))
    content.append(Paragraph(f"<b>Invoice Date:</b> {invoice_date}", normal_style))
    content.append(Spacer(1, 12))

    # Member information
    content.append(Paragraph("Member Information", header_style))
    member_info = [
        ["Name:", member.name],
        ["Email:", member.email],
        ["Phone:", member.phone_number or 'N/A'],
        ["Date of Birth:", member.dob.strftime('%Y-%m-%d') if member.dob else 'N/A'],
        ["Gender:", member.gender or 'N/A'],
        ["Join Date:", member.join_date.strftime('%Y-%m-%d')],
    ]

    member_table = Table(member_info, colWidths=[2*inch, 4*inch])
    member_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    content.append(member_table)
    content.append(Spacer(1, 12))

    # Membership details
    content.append(Paragraph("Membership Details", header_style))
    membership_info = [
        ["Membership Type:", member.membership_type.title()],
        ["Start Date:", member.membership_start_date.strftime('%Y-%m-%d')],
        ["End Date:", member.membership_end_date.strftime('%Y-%m-%d')],
        ["Status:", "Active" if member.is_active else "Inactive"],
    ]

    membership_table = Table(membership_info, colWidths=[2*inch, 4*inch])
    membership_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    content.append(membership_table)
    content.append(Spacer(1, 12))

    # Charges
    content.append(Paragraph("Charges", header_style))
    charges_data = [
        ["Description", "Quantity", "Unit Price", "Total"],
        [f"{member.membership_type.title()} Membership", f"{duration_months} month(s)", f"${price_per_month:.2f}", f"${total_amount:.2f}"],
        ["", "", "Total Amount:", f"${total_amount:.2f}"],
    ]

    charges_table = Table(charges_data, colWidths=[3*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    charges_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (3, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.white),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    content.append(charges_table)
    content.append(Spacer(1, 12))

    # Footer
    content.append(Paragraph("Thank you for choosing our gym!", normal_style))
    content.append(Paragraph("Please keep this invoice for your records.", normal_style))

    # Build PDF
    doc.build(content)
    return response
