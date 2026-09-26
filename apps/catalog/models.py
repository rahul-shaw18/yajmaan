import uuid
from django.db import models


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        db_column='parent_id'
    )
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True)
    icon_url = models.URLField(max_length=1024, null=True, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'categories'
        ordering = ['display_order', 'name']
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} -> {self.name}"
        return self.name


class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)

    class Meta:
        db_table = 'tags'

    def __str__(self):
        return self.name


class Service(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='services',
        db_column='category_id'
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='services',
        db_table='service_tags'
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    banner_image_url = models.URLField(max_length=1024)
    thumbnail_url = models.URLField(max_length=1024, null=True, blank=True)
    duration_text = models.CharField(max_length=64, blank=True)
    duration_minutes_min = models.PositiveIntegerField()
    duration_minutes_max = models.PositiveIntegerField()
    vendors_required = models.PositiveIntegerField(default=1)
    rating_average = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    reviews_count = models.PositiveIntegerField(default=0)
    about = models.TextField()

    # Generic Pricing: standard / without materials vs package / with materials
    price_without_samagri = models.DecimalField(max_digits=10, decimal_places=2)
    price_with_samagri = models.DecimalField(max_digits=10, decimal_places=2)

    # Vertical-specific metadata:
    # Pooja: {"origin_story": "...", "scripture_source": "...", "benefits": [{"title": "...", "description": "..."}]}
    # Barber/Massage: {"equipment": "...", "styles": [...]}
    meta = models.JSONField(default=dict, blank=True)

    is_popular = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'services'
        ordering = ['-rating_average', 'name']

    def __str__(self):
        return f"{self.name} ({self.category.name})"


class PoojaSamagriItem(models.Model):
    """
    Items or materials included for the service (Pooja Samagri, Barber Grooming Kit, Massage Oils, etc.)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='samagri_items',
        db_column='service_id'
    )
    item_name = models.CharField(max_length=128)
    quantity = models.CharField(max_length=64, null=True, blank=True)
    is_included_by_default = models.BooleanField(default=True)

    class Meta:
        db_table = 'pooja_samagri_items'

    def __str__(self):
        return f"{self.item_name} ({self.quantity}) - {self.service.name}"
