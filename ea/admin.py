from django.contrib import admin

from ea.models import Push, Document, Sign, Attachment, DefaulSignList, Invoice, SignList, SignGroup, Cc

admin.site.register(Push)
admin.site.register(Invoice)
admin.site.register(Document)
admin.site.register(Attachment)
admin.site.register(Sign)
admin.site.register(DefaulSignList)
admin.site.register(SignList)
admin.site.register(SignGroup)
admin.site.register(Cc)











