from datetime import date, datetime, time
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from django.db.models import Q, QuerySet, Sum

from ea.models import Document, Attachment, Sign, SIGN_TYPE, DefaulSignList, Invoice
from employee.models import Employee
from PIL import Image
import os
import json

from typing import List, Union

from erp.services import OracleService

Approvers = List[dict]


def update_batch_number(batch_number: int):
    """
    ERP Update Query 실행 : 일괄 적용
    """
    pass


def create_date(date_str: str) -> date:
    date_list: list = date_str.split('-')
    return date(int(date_list[0]), int(date_list[1]), int(date_list[2]))


def create_date_str(date_list: str) -> str:
    start_date: list = date_list.split('-')
    start_date: str = start_date[0] + start_date[1] + start_date[2]
    return start_date


def filter_document(documents: QuerySet, search: str, batch_number: str,
                    user: str, department: str) -> QuerySet:
    if search:
        documents = documents.filter(title__contains=search)

    if batch_number:
        documents = documents.filter(batch_number=batch_number)

    if user:
        documents = documents.filter(author__first_name__contains=user)

    if department:
        documents = documents.filter(author__employee__department__name__contains=department)

    documents = documents.annotate(price=(Sum('invoices__RPZ5DEBITAT') + Sum('invoices__RPZ5CREDITAT')) / 2)
    return documents


@transaction.atomic
class DocumentServices:
    def __init__(self, **kwargs):
        attachments: list = kwargs.get('attachments')
        attachments_invoices: list = kwargs.get('attachments_invoices')
        attachments_counts: list = kwargs.get('attachments_counts')
        title: str = kwargs.get('title')
        batch_number: int = kwargs.get('batch_number')
        document_type: str = kwargs.get('document_type')
        approvers: Approvers = kwargs.get('approvers')
        author: User = kwargs.get('author')

        document: Document = self.create_document(title, author, approvers, batch_number, document_type)

        self.create_invoices(document)

        for invoice_id in attachments_invoices:
            """
            invoice's attachments create
            """
            attachment_count = int(attachments_counts[0])
            if attachment_count > 0:
                invoice_attachments = attachments[0:attachment_count]
                del attachments[0:attachment_count]
                # self.create_attachments(invoice_attachments, Invoice.objects.get(IDS=invoice_id), document)
                self.create_attachments(invoice_attachments,
                                        Invoice.objects.filter(Q(IDS=invoice_id), ~Q(document__doc_status=2)).first(),
                                        document)
            attachments_counts.pop(0)

        DefaulSignList.objects.filter(Q(user=author), Q(document_type=document.document_type)).delete()

        for i, approver in enumerate(approvers):
            """
            approvers 순서대로 왔다고 가정
            """
            user: User = User.objects.get(username=approver.get('id'))
            self.create_sign(user, i, document, approver.get('type'))
            self.create_defaulsignlist(author, user.employee, approver.get('type'), i, document.document_type)

        # self.send_push(document)

    def create_document(self, title: str, auhor: User, approvers: Approvers,
                        batch_number: int, document_type: str) -> Document:
        sign_list: str = ''
        for approver in approvers:
            sign_list += f'{approver.get("name")} ->'

        doc_type: str = '0'
        if document_type == '채무정리':
            doc_type = '1'
        elif document_type == '채권발생':
            doc_type = '2'
        elif document_type == '채권정리':
            doc_type = '3'
        elif document_type == '일반전표':
            doc_type = '4'

        return Document.objects.create(
            author=auhor,
            title=title,
            sign_list=sign_list,
            batch_number=batch_number,
            document_type=doc_type
        )

    def create_attachments(self, attachments: list, invoice: Invoice, document: Document) -> None:
        for attachment in attachments:
            fs = FileSystemStorage(location=settings.MEDIA_ROOT + '/attachment/')
            # current_time = datetime.now().strftime('%Y%m%d') + '_'
            filename = fs.save(attachment.name, attachment)
            size = attachment.size
            is_img = False
            is_pdf = False

            if 'image' in attachment.content_type:
                # if attachment.size > 500000:  # 500KB 보다 크면 용량 줄이기
                os.chdir(fs.location)
                image = Image.open(filename)
                image.save(filename, quailty=50)
                #os.chmod(filename, 0o777)
                size = len(Image.open(filename).fp.read())
                is_img = True

            if 'pdf' in attachment.content_type:
                is_pdf = True

            Attachment.objects.create(
                invoice=invoice,
                document=document,
                title=filename,
                size=size,
                path='attachment/' + filename,
                isImg=is_img,
                isPdf=is_pdf
            )

    def create_invoices(self, document: Document) -> None:
        if document.document_type == '1':
            invoices: list = Invoice.query_batch_invoices([f" RPICU={document.batch_number} "], 'vap_payment1')
        elif document.document_type == '2':
            invoices: list = Invoice.query_batch_invoices([f" RPICU={document.batch_number} "], 'var_invoice1')
        elif document.document_type == '3':
            invoices: list = Invoice.query_batch_invoices([f" RPICU={document.batch_number} "], 'var_receipt1')
        elif document.document_type == '4':
            invoices: list = Invoice.query_batch_invoices([f" RPICU={document.batch_number} "], 'vga_nacct1')
        else:
            invoices: list = Invoice.query_batch_invoices([f" RPICU={document.batch_number} "])

        document_temp: dict = {'document': document}
        for invoice in invoices:
            invoice_data = {**invoice, **document_temp}
            Invoice.objects.create(**invoice_data).save()

    def create_sign(self, user: User, seq: int, document: Document, approve_type: str) -> None:
        result = Sign.get_result_type_by_seq(seq)
        Sign.objects.create(
            user=user,
            document=document,
            seq=seq,
            type=approve_type,
            result=result
        )

    def create_defaulsignlist(self, user: User, approver: Employee, type: int,
                              order: int, document_type: str) -> None:
        return DefaulSignList.objects.create(
            user=user,
            approver=approver,
            type=type,
            document_type=document_type,
            order=order
        )

    def send_push(self, document: Document):
        sign: Sign = Sign.objects.filter(Q(document=document), Q(result=0)).first()
        pushs = sign.user.push_data.all()
        for push in pushs:
            push.send_push(f'[결재] {document.title}')
