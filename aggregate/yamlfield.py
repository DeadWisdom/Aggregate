import yaml
from django.db import models
from django import forms
 
class YAMLWidget(forms.Textarea):
    def render(self, name, value, attrs=None):
        if value is None:
            return super(YAMLWidget, self).render(name, None, attrs)
        if not isinstance(value, basestring):
            lines = []
            for k, v in value.items():
                if isinstance(v, basestring):
                    lines.append('%s: %s' % (k, v))
                else:
                    lines.append('%s: %s' % (k, yaml.safe_dump(v)))
            value = "\n".join(lines)
        if not attrs:
            attrs = {}
        attrs['style'] = 'width: 500px'
        return super(YAMLWidget, self).render(name, value, attrs)
 
class YAMLFormField(forms.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['widget'] = YAMLWidget
        super(YAMLFormField, self).__init__(*args, **kwargs)
 
    def clean(self, value):
        if not value: return
        try:
            return yaml.load(value)
        except Exception, exc:
            raise forms.ValidationError(u'YAML decode error: %s' % (unicode(exc),))
 
class YAMLField(models.TextField):
    __metaclass__ = models.SubfieldBase
 
    def formfield(self, **kwargs):
        return super(YAMLField, self).formfield(form_class=YAMLFormField, **kwargs)
 
    def to_python(self, value):
        if isinstance(value, basestring):
            value = yaml.load(value)
        return value
 
    def get_db_prep_save(self, value):
        if value is None: return
        return yaml.dump(value)
 
    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)