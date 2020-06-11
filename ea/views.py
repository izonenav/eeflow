import json
from datetime import date, datetime, time
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q, QuerySet, Sum, Count, Case, When
from django.http import HttpResponse, HttpRequest
from typing import List

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.request import Request

from ea.models import Push, Document, Attachment, Sign, SIGN_TYPE, DefaulSignList, DOCUMENT_TYPE
from ea.serializers import DefaultUsersSerializer, SignUsersSerializer, DocumentSerializer, PushSerializer
from ea.services import DocumentServices, Approvers, create_date, filter_document

from employee.models import Department, Employee
from erp.services import OracleService


def send_push(request: HttpRequest):
    if request.method == 'POST':
        pushes: List[Push] = request.user.push_data.all()
        for push in pushes:
            push.send_push('이승우짱!!!')
        return HttpResponse('<H1>HI</H1>')


@api_view(['POST'])
def create_push(request: Request):
    push_info: dict = request.data.get('pushInfo')
    data = {'user': request.user.id,
            'endpoint': push_info.get('endpoint'),
            'p256dh': push_info.get('keys').get('p256dh'),
            'auth': push_info.get('keys').get('auth')}

    if Push.objects.filter(endpoint=push_info.get('endpoint')):
        return Response(status=status.HTTP_200_OK)

    serializer = PushSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def check_push(request: Request):
    endpoint: str = request.query_params.get('endpoint')

    if Push.objects.filter(Q(endpoint=endpoint), Q(user=request.user)):
        return Response(status=status.HTTP_200_OK)

    return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def delete_push(request: Request):
    endpoint: str = request.data.get('endpoint')
    push: Push = Push.objects.filter(endpoint=endpoint).first()

    if not push:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    push.delete()
    return Response(status=status.HTTP_200_OK)


@api_view(['POST'])
def create_document(request: Request):
    author: User = request.user
    title: str = request.data.get('title')
    batch_number: int = request.data.get('batch_number')
    document_type: str = request.data.get('document_type')
    approvers: str = request.data.get('approvers')
    approvers: Approvers = json.loads(approvers)
    attachments_files: list = request.FILES.getlist('files')
    attachments_counts: list = request.POST.getlist('counts')
    attachments_invoices: list = request.POST.getlist('invoices')

    if Document.objects.filter(Q(batch_number=batch_number), ~Q(doc_status=2)).first():
        return Response(status=status.HTTP_400_BAD_REQUEST)

    DocumentServices(attachments=attachments_files,
                     attachments_invoices=attachments_invoices,
                     attachments_counts=attachments_counts,
                     title=title,
                     batch_number=batch_number,
                     document_type=document_type,
                     approvers=approvers,
                     author=author)

    service = OracleService()
    service.execute_insert_query('kcfeed.eabatno',
                                 ['BATNO', 'BATDT'], [batch_number, datetime.now().strftime("%Y%m%d")])

    return Response(status=status.HTTP_201_CREATED)


@api_view(['GET'])
def get_defaultUsers(request: Request, document_type: str):
    doc_type = '0'
    for t in DOCUMENT_TYPE:
        if document_type == t[1]:
            doc_type = t[0]
            break

    defaulSignList = DefaulSignList.objects.filter(Q(user=request.user), Q(document_type=doc_type))
    serializer = DefaultUsersSerializer(defaulSignList, many=True)
    return Response(data=serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_departmentUsers(request: Request):
    # department = Department.objects.get(name=department_name)
    employees = Employee.objects.filter(department=request.user.employee.department)
    serializer = SignUsersSerializer(employees, many=True)
    return Response(data=serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def allUsers(request: Request):
    employees = Employee.objects.all()
    serializer = SignUsersSerializer(employees, many=True)
    return Response(data=serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_todo_count(request: Request):
    documents_count: int = Document.objects.filter(
        Q(signs__result=0),
        Q(signs__user=request.user)).count()

    return Response(data=documents_count, status=status.HTTP_200_OK)


@api_view(['GET'])
def written_document(request: Request):
    paginator = PageNumberPagination()
    paginator.page_size = 25

    start_date: date = create_date(request.query_params.get('startDate'))
    end_date: date = create_date(request.query_params.get('endDate'))
    search: str = request.query_params.get('search')
    batch_number: str = request.query_params.get('batchNumber', '')
    user: str = request.query_params.get('user', '')
    department: str = request.query_params.get('department', '')

    documents: QuerySet = Document.objects.filter(
        Q(author=request.user),
        Q(created__range=(datetime.combine(start_date, time.min),
                          datetime.combine(end_date, time.max))))

    documents = filter_document(documents, search, batch_number, user, department)
    total_number = documents.count()
    documents = paginator.paginate_queryset(documents, request)

    serializer = DocumentSerializer(documents, many=True)
    return Response(data=serializer.data + [{'total_number': total_number}], status=status.HTTP_200_OK)


@api_view(['GET'])
def approved_document(request: Request):
    paginator = PageNumberPagination()
    paginator.page_size = 25

    start_date: date = create_date(request.query_params.get('startDate'))
    end_date: date = create_date(request.query_params.get('endDate'))
    search: str = request.query_params.get('search')
    batch_number: str = request.query_params.get('batchNumber', '')
    user: str = request.query_params.get('user', '')
    department: str = request.query_params.get('department', '')

    documents: QuerySet = Document.objects.filter(
        Q(signs__result__in=[2, 3]),
        Q(signs__user=request.user),
        Q(created__range=(datetime.combine(start_date, time.min),
                          datetime.combine(end_date, time.max))))

    documents = filter_document(documents, search, batch_number, user, department)
    total_number = documents.count()
    documents = paginator.paginate_queryset(documents, request)

    serializer = DocumentSerializer(documents, many=True)

    return Response(data=serializer.data + [{'total_number': total_number}], status=status.HTTP_200_OK)


@api_view(['GET'])
def document(request: Request):
    document_id: date = request.query_params.get('document_id')
    document: Document = Document.objects.get(id=document_id)
    serializer = DocumentSerializer(document)
    return Response(data=serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def rejected_document(request: Request):
    paginator = PageNumberPagination()
    paginator.page_size = 25

    start_date: date = create_date(request.query_params.get('startDate'))
    end_date: date = create_date(request.query_params.get('endDate'))
    search: str = request.query_params.get('search')
    batch_number: str = request.query_params.get('batchNumber', '')
    user: str = request.query_params.get('user', '')
    department: str = request.query_params.get('department', '')

    documents: QuerySet = Document.objects.filter(
        Q(signs__result=3),
        Q(author__username=request.user),
        Q(created__range=(datetime.combine(start_date, time.min),
                          datetime.combine(end_date, time.max))))

    documents = filter_document(documents, search, batch_number, user, department)
    total_number = documents.count()
    documents = paginator.paginate_queryset(documents, request)

    serializer = DocumentSerializer(documents, many=True)
    return Response(data=serializer.data + [{'total_number': total_number}], status=status.HTTP_200_OK)


@api_view(['GET'])
def sign_document(request: Request):
    start_date: date = create_date(request.query_params.get('startDate'))
    end_date: date = create_date(request.query_params.get('endDate'))

    search: str = request.query_params.get('search', '')
    batch_number: str = request.query_params.get('batchNumber', '')
    user: str = request.query_params.get('user', '')
    department: str = request.query_params.get('department', '')

    documents = Document.objects.filter(
        Q(signs__result=0),
        Q(signs__user__username=request.user),
        Q(created__range=(datetime.combine(start_date, time.min),
                          datetime.combine(end_date, time.max))))

    if search:
        documents = documents.filter(Q(title__contains=search) | Q(author__first_name__contains=search))

    documents = documents.annotate(price=(Sum('invoices__RPZ5DEBITAT') + Sum('invoices__RPZ5CREDITAT')) / 2)
    documents = documents.annotate(invoices_count=Case(
        When(document_type='0', then=Count('invoices', filter=Q(invoices__RPSEQ=1, invoices__RPSFX='001'))),
        When(document_type='2', then=Count('invoices', filter=Q(invoices__RPSEQ=1, invoices__RPSFX='001'))),
        When(document_type='3', then=Count('invoices__RPCKNU', distinct=True)),
        default=Count('invoices', filter=Q(invoices__RPSEQ=1))
    ))
    serializer = DocumentSerializer(documents, many=True)
    return Response(data=serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
def do_sign(request: Request):
    document_id: int = request.data.get('document_id')
    username: str = request.data.get('username')
    opinion: str = request.data.get('opinion')
    sign_type: str = request.data.get('sign_type')

    document: Document = Document.objects.get(id=document_id)
    sign: Sign = document.signs.get(user__username=username)
    sign.approve_sign(opinion) if sign_type == '승인' else sign.deny_sign(opinion)

    return Response(status=status.HTTP_200_OK)


@api_view(['POST'])
@transaction.atomic
def do_sign_all(request: Request):
    document_ids: list = request.data.get('document_ids')

    for document_id in document_ids:
        document: Document = Document.objects.get(id=document_id)
        sign: Sign = document.signs.first().get_stand_by_sign()
        sign.approve_sign('')

    return Response(status=status.HTTP_200_OK)
