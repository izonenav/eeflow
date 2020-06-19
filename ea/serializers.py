from rest_framework import serializers

from ea.models import DefaulSignList, Document, Attachment, Sign, Push, Invoice, SignGroup, SignList
from employee.models import Employee


class DefaultUsersSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='approver.user.username')
    name = serializers.CharField(source='approver.user.first_name')
    avatar = serializers.ImageField(source='approver.avatar')
    department = serializers.CharField(source='approver.department.name')
    position = serializers.CharField(source='approver.position.name')

    class Meta:
        model = DefaulSignList
        fields = ['id', 'name', 'avatar', 'department', 'position', 'type', 'order']


class SignUsersSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='user.username')
    name = serializers.CharField(source='user.first_name')
    department = serializers.CharField(source='department.name')
    position = serializers.CharField(source='position.name')
    type = serializers.SerializerMethodField(read_only=True)
    order = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Employee
        fields = ['id', 'name', 'avatar', 'department', 'position', 'type', 'order']

    def get_type(self, obj: Employee):
        return '0'

    def get_order(self, obj: Employee):
        return obj.get_order()


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = '__all__'


class SignSerializer(serializers.ModelSerializer):
    user = SignUsersSerializer(source='user.employee', read_only=True)

    class Meta:
        model = Sign
        fields = '__all__'


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = '__all__'


class DocumentSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.first_name')
    author_id = serializers.CharField(source='author.username')
    department = serializers.CharField(source='author.employee.department.name')
    created = serializers.DateTimeField(format='%Y-%m-%d')
    doc_status = serializers.CharField(source='get_doc_status_display')
    document_type = serializers.CharField(source='get_document_type_display')
    attachments = AttachmentSerializer(read_only=True, many=True)
    invoices = InvoiceSerializer(read_only=True, many=True)
    signs = SignSerializer(read_only=True, many=True)
    price = serializers.IntegerField(read_only=True)
    invoices_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Document
        fields = ['id', 'title', 'author', 'author_id', 'department', 'doc_status', 'created', 'batch_number',
                  'document_type', 'attachments', 'invoices', 'signs', 'price', 'invoices_count']


class PushSerializer(serializers.ModelSerializer):
    class Meta:
        model = Push
        fields = '__all__'


class SignListSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='approver.user.first_name')
    avatar = serializers.ImageField(source='approver.avatar')
    department = serializers.CharField(source='approver.department.name')
    position = serializers.CharField(source='approver.position.name')
    id = serializers.CharField(source='approver.user.username')

    class Meta:
        model = SignList
        fields = '__all__'


class SignGroupSerializer(serializers.ModelSerializer):
    sign_lists = SignListSerializer(read_only=True, many=True)

    class Meta:
        model = SignGroup
        fields = '__all__'
