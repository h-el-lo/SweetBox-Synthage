from django import forms

class SketchUploadForm(forms.Form):
    sketch = forms.FileField(
        label="Upload .ino Sketch",
        widget = forms.ClearableFileInput(
            attrs={
                'accept':'.ino'
            }
        )
    )
