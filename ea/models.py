import os

from django.contrib.auth.models import User, Group
from django.core.files.storage import FileSystemStorage
from django.db import models
from typing import Union

from pywebpush import webpush, WebPushException

from django.conf import settings
from django.utils import timezone

from employee.models import Employee, Department
from erp.services import OracleService
from PIL import Image

DELETE_STATE_CHOICES = (
    ('Y', '삭제됨'),
    ('N', '미삭제'),
)

DOC_STATUS = (
    ('0', '임시저장'),
    ('1', '결재대기중'),
    ('2', '반려'),
    ('3', '결재완료'),
)

SIGN_RESULT = (
    ('0', '대기중'),
    ('1', '다음대기'),
    ('2', '승인'),
    ('3', '반려'),
)

SIGN_TYPE = (
    ('0', '결재'),
    ('1', '합의'),
    ('2', '수신참조'),
)

DOCUMENT_TYPE = (
    ('0', '채무발생'),
    ('1', '채무정리'),
    ('2', '채권발생'),
    ('3', '채권정리'),
    ('4', '일반전표'),
)


class TimeStampedModel(models.Model):
    """
        created , modified field 제공해주는 abstract base class model
    """

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Push(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_data')
    endpoint = models.TextField()
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)

    objects = models.Manager()

    def get_subscription_info(self) -> dict:
        return {"endpoint": self.endpoint, "keys": {"p256dh": self.p256dh, "auth": self.auth}}

    def send_push(self, content: str) -> None:
        try:
            webpush(
                subscription_info=self.get_subscription_info(),
                data=content,
                vapid_private_key=settings.PUSH_PRIVATE_KEY,
                vapid_claims={
                    "sub": "mailto:leemoney93@naver.com",
                }
            )
        except WebPushException as ex:
            print("I'm sorry, Dave, but I can't do that: {}", repr(ex))

    def __str__(self):
        return self.user.username


class Document(TimeStampedModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='document')
    document_type = models.CharField(
        max_length=2,
        choices=DOCUMENT_TYPE,
        default='0',
    )
    title = models.CharField(max_length=255)
    delete_state = models.CharField(
        max_length=2,
        choices=DELETE_STATE_CHOICES,
        default='N',
    )
    doc_status = models.CharField(
        max_length=2,
        choices=DOC_STATUS,
        default='1',
    )
    sign_list = models.CharField(max_length=255)
    batch_number = models.PositiveIntegerField()
    is_readed_after_finishing = models.BooleanField(default=False)

    def finish_deny(self, push_content: str) -> None:
        """
        작성자에게 결재완료 notify
        for push in self.author.push_data.all():
            push.send_push(push_content)

        crontab으로 대체 하지 않음
        """
        self.doc_status = '2'
        self.save()

        for push in self.author.push_data.all():
            push.send_push(push_content)

    def finish_approve(self, push_content: str) -> None:
        """
        작성자에게 결재완료 notify
        for push in self.author.push_data.all():
            push.send_push(push_content)

        기능 OFF
        """
        self.doc_status = '3'
        self.save()

        if len(self.invoices.first().RPPOST.strip()) != 0:  # RPPOST 값이 blank(기 전기된 전표)면 Update를 하지 않음
            return

        yyyy, mm, dd = self.invoices.first().RPDGJ.split('-')
        if yyyy + mm + dd >= '20200701':  # TODO 초기 한달만 운영
            self.update_document_to_erp()

    def update_document_to_erp(self) -> None:
        """
        최종결재 후 해당 배치번호 update
        :return:
        """
        oracle = OracleService()
        query = f" UPDATE PRODDTA.F0011 SET ICIST = 'A', ICPID = 'AUTOPOST' WHERE ICICU = {self.batch_number} "
        oracle.execute_update_query(query)

    def __str__(self):
        return f'{self.title}({self.author.first_name})'


class Invoice(TimeStampedModel):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='invoices')
    IDS = models.CharField(max_length=100)
    RPCO = models.CharField(max_length=100, null=True, blank=True)
    RPICU = models.CharField(max_length=30, null=True, blank=True)
    RPDOC = models.CharField(max_length=50, null=True, blank=True)
    RPICUT = models.CharField(max_length=10, null=True, blank=True)
    RPDCT = models.CharField(max_length=10, null=True, blank=True)
    RPDICJ = models.CharField(max_length=10, null=True, blank=True)
    RPDGJ = models.CharField(max_length=10, null=True, blank=True)
    RPSEQ = models.IntegerField(null=True, blank=True)
    RPAN8 = models.IntegerField(null=True, blank=True)
    RPALPH = models.CharField(max_length=80, null=True, blank=True)
    RPTAX = models.CharField(max_length=200, null=True, blank=True)
    RPPOST = models.CharField(max_length=2, null=True, blank=True)
    RPMCU = models.CharField(max_length=24, null=True, blank=True)
    RPOBJ = models.CharField(max_length=12, null=True, blank=True)
    RPSUB = models.CharField(max_length=20, null=True, blank=True)
    RPCODE = models.CharField(max_length=56, null=True, blank=True)
    RPDL02 = models.TextField(null=True, blank=True)
    RPZ5DEBITAT = models.IntegerField(null=True, blank=True)
    RPZ5CREDITAT = models.IntegerField(null=True, blank=True)
    RPDC = models.TextField(null=True, blank=True)
    RPRMK = models.CharField(max_length=60, null=True, blank=True)
    RPTORG = models.CharField(max_length=20, null=True, blank=True)
    RPNAME = models.TextField(null=True, blank=True)
    RPDSVJ = models.CharField(max_length=10, null=True, blank=True)
    RPEXR1 = models.CharField(max_length=4, null=True, blank=True)
    RPTXA1 = models.CharField(max_length=20, null=True, blank=True)
    RPEXR1NM = models.TextField(null=True, blank=True)
    RPPO = models.CharField(max_length=16, null=True, blank=True)
    RPASID = models.CharField(max_length=50, null=True, blank=True)
    RPPDCT = models.CharField(max_length=4, null=True, blank=True)
    RPSBLT = models.CharField(max_length=2, null=True, blank=True)
    RPADDN = models.TextField(null=True, blank=True)
    RPDL03 = models.TextField(null=True, blank=True)
    RPPYE = models.IntegerField(null=True, blank=True)
    RPGLC = models.CharField(max_length=2, null=True, blank=True)
    RPDDJ = models.CharField(max_length=10, null=True, blank=True)
    RPJELN = models.CharField(max_length=10, null=True, blank=True)
    RPSFX = models.CharField(max_length=6, null=True, blank=True)
    # other
    RPDOCM = models.CharField(max_length=100, null=True, blank=True)
    RPVLDT = models.CharField(max_length=100, null=True, blank=True)
    RPVINV = models.CharField(max_length=100, null=True, blank=True)
    RPPST = models.CharField(max_length=100, null=True, blank=True)
    RPDIVJ = models.CharField(max_length=100, null=True, blank=True)
    RPDL04 = models.CharField(max_length=100, null=True, blank=True)
    RPDKJ = models.CharField(max_length=100, null=True, blank=True)
    RPPYID = models.CharField(max_length=100, null=True, blank=True)
    RPRC5 = models.CharField(max_length=100, null=True, blank=True)
    RPTYIN = models.CharField(max_length=100, null=True, blank=True)
    RPDCTM = models.CharField(max_length=100, null=True, blank=True)
    RPCKNU = models.CharField(max_length=100, null=True, blank=True)
    RPDMTJ = models.CharField(max_length=100, null=True, blank=True)
    RPGLBA = models.CharField(max_length=100, null=True, blank=True)
    RPICUA = models.CharField(max_length=100, null=True, blank=True)
    RPAID = models.CharField(max_length=100, null=True, blank=True)
    RPB76ERN = models.CharField(max_length=100, null=True, blank=True)
    RPDL05 = models.CharField(max_length=100, null=True, blank=True)
    RPNFVD = models.CharField(max_length=100, null=True, blank=True)
    RPPN = models.CharField(max_length=100, null=True, blank=True)
    RPSBL = models.CharField(max_length=100, null=True, blank=True)
    RPEXR = models.CharField(max_length=100, null=True, blank=True)
    RPEXA = models.CharField(max_length=100, null=True, blank=True)
    RPRE = models.CharField(max_length=100, null=True, blank=True)
    RPLITM = models.TextField(null=True, blank=True)

    def __str__(self):
        return f'{self.RPDGJ}({self.RPRMK})'

    QUERY_COLUMS = [
        {'IDS': 'IDS'},
        {'RPCO': 'RPCO'},
        {'RPICU': 'RPICU'},
        {'RPDOC': 'RPDOC'},
        {'RPICUT': 'RPICUT'},
        {'RPDCT': 'RPDCT'},
        {'RPDICJ': 'RPDICJ'},
        {'RPDGJ': 'RPDGJ'},
        {'RPSEQ': 'RPSEQ'},
        {'RPAN8': 'RPAN8'},
        {'RPALPH': 'RPALPH'},
        {'RPTAX': 'RPTAX'},
        {'RPPOST': 'RPPOST'},
        {'RPMCU': 'RPMCU'},
        {'RPOBJ': 'RPOBJ'},
        {'RPSUB': 'RPSUB'},
        {'RPCODE': 'RPCODE'},
        {'RPDL02': 'RPDL02'},
        {'RPDC': 'RPDC'},
        {'RPRMK': 'RPRMK'},
        {'RPTORG': 'RPTORG'},
        {'RPNAME': 'RPNAME'},
        {'RPDSVJ': 'RPDSVJ'},
        {'RPEXR1': 'RPEXR1'},
        {'RPTXA1': 'RPTXA1'},
        {'RPEXR1NM': 'RPEXR1NM'},
        {'RPPO': 'RPPO'},
        {'RPASID': 'RPASID'},
        {'RPPDCT': 'RPPDCT'},
        {'RPSBLT': 'RPSBLT'},
        {'RPADDN': 'RPADDN'},
        {'RPDL03': 'RPDL03'},
        {'RPPYE': 'RPPYE'},
        {'RPGLC': 'RPGLC'},
        {'RPDDJ': 'RPDDJ'},
        {'RPJELN': 'RPJELN'},
        {'RPSFX': 'RPSFX'},
        # other
        {'RPDOCM': 'RPDOCM'},
        {'RPVLDT': 'RPVLDT'},
        {'RPVINV': 'RPVINV'},
        {'RPPST': 'RPPST'},
        {'RPDIVJ': 'RPDIVJ'},
        {'RPDL04': 'RPDL04'},
        {'RPDKJ': 'RPDKJ'},
        {'RPPYID': 'RPPYID'},
        {'RPRC5': 'RPRC5'},
        {'RPTYIN': 'RPTYIN'},
        {'RPDCTM': 'RPDCTM'},
        {'RPCKNU': 'RPCKNU'},
        {'RPDMTJ': 'RPDMTJ'},
        {'RPGLBA': 'RPGLBA'},
        {'RPICUA': 'RPICUA'},
        {'RPAID': 'RPAID'},
        {'RPB76ERN': 'RPB76ERN'},
        {'RPDL05': 'RPDL05'},
        {'RPNFVD': 'RPNFVD'},
        {'RPPN': 'RPPN'},
        {'RPSBL': 'RPSBL'},
        {'RPEXR': 'RPEXR'},
        {'RPEXA': 'RPEXA'},
        {'RPRE': 'RPRE'},
        {'RPLITM': 'RPLITM'},
        # 차변, 대변
        {'RPZ5DEBITAT / 100': 'RPZ5DEBITAT'},
        {'RPZ5CREDITAT / 100': 'RPZ5CREDITAT'},
    ]

    QUERY_COLUMS_NORMAL = [
        {'IDS': 'IDS'},
        {'RPCO': 'RPCO'},
        {'RPICU': 'RPICU'},
        {'RPDOC': 'RPDOC'},
        {'RPICUT': 'RPICUT'},
        {'RPDCT': 'RPDCT'},
        {'RPDICJ': 'RPDICJ'},
        {'RPDGJ': 'RPDGJ'},
        {'RPSEQ': 'RPSEQ'},
        {'RPAN8': 'RPAN8'},
        {'RPALPH': 'RPALPH'},
        {'RPTAX': 'RPTAX'},
        {'RPPOST': 'RPPOST'},
        {'RPMCU': 'RPMCU'},
        {'RPOBJ': 'RPOBJ'},
        {'RPSUB': 'RPSUB'},
        {'RPCODE': 'RPCODE'},
        {'RPDL02': 'RPDL02'},
        {'RPDC': 'RPDC'},
        {'RPRMK': 'RPRMK'},
        {'RPTORG': 'RPTORG'},
        {'RPNAME': 'RPNAME'},
        {'RPDSVJ': 'RPDSVJ'},
        {'RPEXR1': 'RPEXR1'},
        {'RPTXA1': 'RPTXA1'},
        {'RPEXR1NM': 'RPEXR1NM'},
        {'RPPO': 'RPPO'},
        {'RPASID': 'RPASID'},
        {'RPPDCT': 'RPPDCT'},
        {'RPSBLT': 'RPSBLT'},
        {'RPADDN': 'RPADDN'},
        {'RPDL03': 'RPDL03'},
        {'RPPYE': 'RPPYE'},
        {'RPGLC': 'RPGLC'},
        {'RPDDJ': 'RPDDJ'},
        {'RPJELN': 'RPJELN'},
        {'RPSFX': 'RPSFX'},
        # other
        {'RPDOCM': 'RPDOCM'},
        {'RPVLDT': 'RPVLDT'},
        {'RPVINV': 'RPVINV'},
        {'RPPST': 'RPPST'},
        {'RPDIVJ': 'RPDIVJ'},
        {'RPDL04': 'RPDL04'},
        {'RPDKJ': 'RPDKJ'},
        {'RPPYID': 'RPPYID'},
        {'RPRC5': 'RPRC5'},
        {'RPTYIN': 'RPTYIN'},
        {'RPDCTM': 'RPDCTM'},
        {'RPCKNU': 'RPCKNU'},
        {'RPDMTJ': 'RPDMTJ'},
        {'RPGLBA': 'RPGLBA'},
        {'RPICUA': 'RPICUA'},
        {'RPAID': 'RPAID'},
        {'RPB76ERN': 'RPB76ERN'},
        {'RPDL05': 'RPDL05'},
        {'RPNFVD': 'RPNFVD'},
        {'RPPN': 'RPPN'},
        {'RPSBL': 'RPSBL'},
        {'RPEXR': 'RPEXR'},
        {'RPEXA': 'RPEXA'},
        {'RPRE': 'RPRE'},
        {'RPLITM': 'RPLITM'},
        # 차변, 대변
        {'RPZ5DEBITAT': 'RPZ5DEBITAT'},
        {'RPZ5CREDITAT': 'RPZ5CREDITAT'},
    ]

    @staticmethod
    def query_invoices(wheres: list):
        columns = Invoice.QUERY_COLUMS
        table = 'vap_voucher1'
        wheres = wheres
        service = OracleService()
        query = service.create_select_query(columns, table, wheres)
        result = service.get_result(query, columns)
        return result

    @staticmethod
    def query_batch_invoices(wheres: list, table='vap_voucher1'):
        columns = Invoice.QUERY_COLUMS
        if table == 'vga_nacct1':
            columns = Invoice.QUERY_COLUMS_NORMAL

        wheres = wheres
        service = OracleService()
        query = service.create_select_query(columns, table, wheres)
        result = service.get_result(query, columns)
        return result


class Attachment(TimeStampedModel):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='attachments')
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='attachments')
    title = models.CharField(max_length=255)
    size = models.PositiveIntegerField()
    path = models.FileField(upload_to='attachment/')
    isImg = models.BooleanField(default=False)
    isPdf = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.title}({self.size}KB)'

    @staticmethod
    def create_attachments(attachments: list, invoice: Invoice, document: Document) -> None:
        for attachment in attachments:
            fs = FileSystemStorage(location=settings.MEDIA_ROOT + '/attachment/')
            filename = fs.save(attachment.name, attachment)
            size = attachment.size
            is_img = False
            is_pdf = False

            if 'image' in attachment.content_type:
                if attachment.size > 2000000:  # 3MB 보다 크면 용량 줄이기
                    os.chdir(fs.location)
                    image = Image.open(filename)
                    image.save(filename, quailty=50)
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


class Sign(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sign')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='signs')
    result = models.CharField(
        max_length=2,
        choices=SIGN_RESULT,
        default='1',
    )
    comment = models.TextField(null=True, blank=True)
    seq = models.PositiveIntegerField()
    type = models.CharField(
        max_length=2,
        choices=SIGN_TYPE,
        default='0',
    )
    sign_date = models.DateTimeField(null=True, blank=True)
    is_pushed = models.BooleanField(default=False)

    def get_next_sign(self) -> Union['Sign', None]:
        return self.__class__.objects.filter(document=self.document, seq=self.seq + 1).first()

    def get_stand_by_sign(self) -> 'Sign':
        return self.__class__.objects.filter(document=self.document, result='0').first()

    @staticmethod
    def get_result_type_by_seq(seq: int) -> SIGN_RESULT:
        if seq == 0:
            return '0'

        return '1'

    def stand_by(self) -> None:
        self.result = '0'

    def approve(self) -> None:
        self.result = '2'

    def deny(self) -> None:
        self.result = '3'

    def notify_next_user(self, content: str) -> None:
        """
        다음대기 user notify Code
        # for push in self.user.push_data.all():
        #     push.send_push(content)

        crontab으로 대체
        :param content:
        :return None:
        """
        self.stand_by()
        self.save()

    def approve_sign(self, comment: str) -> None:
        self.approve()
        self.sign_date = timezone.now()
        if comment:
            self.comment = comment
        self.save()

        next_sign: Sign = self.get_next_sign()

        if next_sign:
            next_sign.notify_next_user(f'[결재요청] {self.document.title}')
        else:
            self.document.finish_approve(f'[결재완료] {self.document.title}')

    def deny_sign(self, comment: str) -> None:
        self.deny()
        self.sign_date = timezone.now()
        if comment:
            self.comment = comment
        self.save()

        service = OracleService()
        service.execute_delete_query('kcfeed.eabatno', self.document.batch_number)

        self.document.finish_deny(f'[반려] {self.document.title}')

    @staticmethod
    def create_sign(user: User, seq: int, document: Document, approve_type: str) -> None:
        result = Sign.get_result_type_by_seq(seq)
        Sign.objects.create(
            user=user,
            document=document,
            seq=seq,
            type=approve_type,
            result=result
        )

    def __str__(self):
        return f'{self.document.title}({self.user.first_name}) {self.seq}번째'


class DefaulSignList(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='default_sign_list')
    approver = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='+')
    document_type = models.CharField(
        max_length=2,
        choices=DOCUMENT_TYPE,
        default='0',
    )
    type = models.CharField(
        max_length=2,
        choices=SIGN_TYPE,
        default='0',
    )
    order = models.PositiveSmallIntegerField()

    def __str__(self):
        return f'{self.user.first_name}_{self.approver.user.first_name}/{self.order}번째'


class SignGroup(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sign_groups')
    name = models.CharField(max_length=255)


class SignList(TimeStampedModel):
    group = models.ForeignKey(SignGroup, on_delete=models.CASCADE, related_name='sign_lists')
    approver = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='+')
    type = models.CharField(
        max_length=2,
        choices=SIGN_TYPE,
        default='0',
    )
    order = models.PositiveSmallIntegerField()

    def __str__(self):
        return f'{self.approver.user.first_name}/{self.order}번째'


class Cc(TimeStampedModel):
    receiver = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='carbon_copys_lists')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='carbon_copys')
    is_readed = models.BooleanField(default=False)

    @staticmethod
    def get_cc_type():
        return 2
