from django.contrib import admin
from models import Source

class SourceAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    exclude = ('updating', 'updates', 'updated')
    list_display = ('__unicode__', 'status')
    actions = ('update',)
    
    def update(self, request, queryset):
        for object in queryset:
            object.update(True)
    update.short_description = "Update the selected sources."
    
admin.site.register(Source, SourceAdmin)