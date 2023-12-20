import datetime
from django.db import models
from theater.models import Room, Seat, PopconsAndDrinks, Voucher
from django.contrib.auth.models import UserManager, AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator, MaxValueValidator, MinValueValidator, MinLengthValidator
from django.urls import reverse
from django_jsonform.models.fields import JSONField
from embed_video.fields import EmbedVideoField
from django.core.exceptions import ValidationError

# class OneTimeUser(models.Model):
#     fullname = models.CharField(max_length=50)
#     email = models.EmailField()
#     number = models.CharField(max_length=15, validators=[
#         RegexValidator(
#             regex='^[0-9]+$',
#             message='Number only'
#         )
#     ])

#     def __str__(self):
#         return self.username

class CustomUserManager(UserManager):
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("You have not provided a valid e-mail address")
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user
    
    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)
    
    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self._create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    fullname = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    number = models.CharField(max_length=15, validators=[
        RegexValidator(
            regex='^[0-9]+$',
            message='Number only'
        )
    ])
    dateBirth = models.DateField(null=True)
    address = models.TextField()
    profile_pic = models.ImageField(default="media/user.jpg", upload_to='media/profile_pics', null=True)
    lastLogin = models.DateTimeField(auto_now_add=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = CustomUserManager()
    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        
    
    def get_full_name(self):
        return self.fullname

    def get_absolute_url(self):
        return reverse('users:detail', kwargs={'fullname': self.fullname})
    
    def __str__(self):
        return self.fullname
    
class Movie(models.Model):
    # languages = (
    #     ('English','English'),
    #     ('Spanish','Spanish'),
    #     ('French','French'),
    #     ('German','German'),
    #     ('Italian','Italian'),
    #     ('Portuguese','Portuguese'),
    #     ('Russian','Russian'),
    #     ('Turkish','Turkish'),
    #     ('Chinese','Chinese'),
    #     ('Japanese','Japanese'),
    #     ('Korean','Korean'),
    #     ('Other','Other'),
    #     )
    title = models.CharField(max_length=200, unique=True)
    genre = models.CharField(max_length=200)
    trailer = EmbedVideoField()
    director = models.CharField(max_length=200, null=True)
    actors = models.ManyToManyField('Actor')
    durationInMinutes = models.PositiveSmallIntegerField()
    release_date = models.DateField()
    # language = models.CharField(choices=languages, max_length=30, blank=True)
    tagline = models.CharField(max_length=300, null=True)
    description = models.TextField()
    posterImage = models.ImageField(upload_to='media/posters/', default="media/user.jpg")
    views = models.PositiveIntegerField(default=0)
    rating = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(5)], default=0)
    isAvailable = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def update_views(self):
        bookings_count = Booking.objects.filter(showtime__movie=self).count()
        self.views = bookings_count
        self.save()

    def update_rating(self):
        evaluations = Evulation.objects.filter(movie=self)
        if evaluations.exists():
            total_rating = sum([evaluation.rate for evaluation in evaluations])
            average_rating = total_rating / len(evaluations)
            self.rating = round(average_rating, 2)
        else:
            # If there are no evaluations, set the rating to 0
            self.rating = 0

        self.save()
    
    def get_absolute_url(self):
        return reverse("movies:detail", kwargs={"id": self.id})
    def __str__(self):
        return f"{self.title} ({self.release_date})"
    
class Actor(models.Model):
    name = models.CharField(max_length=30, unique=True)
    image = models.ImageField(upload_to='media/actors/', default="media/user.jpg")
    character = models.CharField(max_length=100, null=True)

    # def get_absolute_url(self):
    #     return reverse("movies:actor-detail", kwargs={"id": self.id})
        
    def __str__(self):
        return self.name
        
class Evulation(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    rate = models.IntegerField(validators=[MinValueValidator(1),MaxValueValidator(5)],help_text='Rate from 1 to 5')
    comment = models.TextField(max_length=400)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    @property
    def idMovie(self):
        return self.movie.id
    
    @property
    def idUser(self):
        return self.user.id
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.movie.update_rating()
    
    def __str__(self):
        return f'Evaluation by {self.user.fullname}, for {self.movie.title}: "{self.comment}" '
    
class Showtimes(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    roomNumber = models.ForeignKey(Room, on_delete=models.CASCADE)
    showtime = models.DateField()
    time = JSONField(
        default=list,
        schema={
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "starttime": {"type": "string", "format": "time"},
                    "endtime": {"type": "string", "format": "time"},
                },
                "required": ["starttime", "endtime"],
            },
            "minItems": 0,
            "maxItems": 10,
        },
    )
    available = models.BooleanField(default=True)

    @property
    def titleMovie(self):
        return self.movie.title

    def __str__(self):
        return f"Showing {self.movie.title} at {self.showtime}"

class Booking(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    fullname = models.CharField(max_length=50, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    number = models.CharField(max_length=15, validators=[
        RegexValidator(
            regex='^[0-9]+$',
            message='Number only'
        )
    ], null=True, blank=True)
    showtime = models.ForeignKey(Showtimes, on_delete=models.CASCADE)
    seat = models.ManyToManyField(Seat)
    voucher = models.ForeignKey(Voucher, on_delete=models.SET_NULL, null=True, blank=True)
    snacks = models.ForeignKey(PopconsAndDrinks, on_delete=models.SET_NULL, null=True, blank=True)
    bookedAt = models.DateTimeField(auto_now_add=True)
    totalPrice = models.DecimalField(decimal_places=2, max_digits=8)
    expiresIn = models.IntegerField(default='210') # in minutes
    paypal_payment_id = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(max_length=30, choices=(('Pending','Pending'), ('Successful','Successful'), ('Failed','Failed')), default='Pending')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.showtime.movie.update_views()

    def clean(self):
        # Check if both user and fullname are empty
        if not self.user and not (self.fullname and self.email and self.number):
            raise ValidationError("Either 'user' or 'fullname, email, number' must be provided.")

        # Check if both user and fullname are provided
        if self.user and (self.fullname and self.email and self.number):
            raise ValidationError("Provide either 'user' or 'fullname, email, number', not both.")

    def __str__(self):
        seat_numbers = ', '.join(str(seat.seatNo) for seat in self.seat.all())
        return f'Booking of Seat {seat_numbers} from {self.bookedAt} to {self.expiresIn // 60} hours.'

# class Payment(models.Model):
#     amount = models.DecimalField(decimal_places=2, max_digits=8)
#     transactionId = models.CharField(max_length=30)
#     paymentMethod = models.CharField(max_length=30)
#     paidAt = models.DateTimeField(auto_now_add=True)
#     booking = models.OneToOneField(Booking, on_delete=models.CASCADE, primary_key=True
#                                    , related_name="payment")
    


                



