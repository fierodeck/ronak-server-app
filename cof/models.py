from django.db import models


class Cof(models.Model):
    name = models.CharField(max_length=255, verbose_name='Name')
    quantity = models.IntegerField(default=1, null=True, blank=True, verbose_name='Quantity')
    price_single = models.CharField(max_length=100, null=True, blank=True, verbose_name='Price per unit')
    price_total = models.CharField(max_length=100, null=True, blank=True, verbose_name='Total price')

    image = models.ImageField(upload_to='cof_images/', null=True, blank=True, verbose_name='Image')
    similar_cofs = models.ManyToManyField('self', blank=True, verbose_name='Similar Cofs')
    notes = models.TextField(null=True, blank=True, verbose_name='Notes')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.name:
            self.name = self.name.strip()
        # Auto-calculate total price
        if self.price_single and self.quantity:
            try:
                self.price_total = str(round(float(self.price_single) * int(self.quantity), 2))
            except ValueError:
                pass

    def __str__(self):
        return self.name
