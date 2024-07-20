from django.db import models;
from django.contrib.auth.models import AbstractUser;
from django.utils.timezone import now

class User(AbstractUser):
    # Add additional fields if needed
    pass

class Bus(models.Model):
    bus_names = {
        "HB" : "Horizon Bus",
        "BC" : "Busscar",
        "GBC" : "Gaaga Bus Company",
        "JEC" : "Jaguar Executive Coaches",
        "KC" : "Kampala Coach",
        "MBS" : "Mash Bus Services",
        "MC" : "Modern Coast",
        "QC" : "Queens Coach",
        "UPB": "Uganda Post Bus",
        "KB" : "Kalita Bus",
        "BBC" : "Baby Coach",
        "KH" : "Kampala Hopper",
        "LK" : "Link Bus",
        "NC" : "Nile Coach",
    }


    # name = models.CharField(max_length=100)
    name = models.CharField(max_length=100, choices=bus_names)

    destinations = {
    "WT": "Kasese", # WT - westernmost Point
    "NT": "Arua", # NT - Northernmost Point
    "ET": "Malaba", # ET - Easternmost Point
    "ST": "Kabale", # ST - Southernmost Point
    "CT": "Kampala", # CT - Central / HQ Stage
}
    
    destination = models.CharField(max_length=50, choices=destinations)

    # https://www.theugandaguide.com/getting-around/bus-services

    travel_routes = { #Bus Routes
    "KSE": "Kasese", # WT - westernmost Point
    "AR": "Arua", # NT - Northernmost Point
    "ML": "Malaba", # ET - Easternmost Point
    "KBL": "Kabale", # ST - Southernmost Point
    "KPL": "Kampala", # CT - Central / HQ Stage
    "MB": "Mbarara",
    "CN": "Cyanika",
    "NB": "Nairobi",
    "KG": "Kigali",
    "JB": "Juba",
    "GM": "Goma",
    "GL": "Gulu",
    "SR": "Soroti",
    "MY": "Moyo",
    "KS": "Kisoro",
}
    
    bus_routes = models.CharField(max_length=150, choices=travel_routes)

    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return self.name



class Booking(models.Model):
    bus = models.ForeignKey(Bus, related_name='bookings', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    seats = models.IntegerField()

    def __str__(self):
        return f"Booking by {self.name} for {self.bus.name}"
