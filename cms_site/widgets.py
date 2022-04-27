from django import forms

class ImagePreview(forms.ClearableFileInput):
    template_name = 'forms/admin/widgets/image-preview-input.html'
    def render(self, name, value, attrs=None, renderer=None):
        return super().render(name, value, attrs, renderer)
