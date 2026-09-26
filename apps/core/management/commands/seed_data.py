import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from apps.accounts.models import User, UserAddress, UserDevice
from apps.catalog.models import Category, Service, PoojaSamagriItem, Tag
from apps.vendors.models import Vendor, VendorDevice
from apps.devotional.models import Arti, Horoscope


class Command(BaseCommand):
    help = "Seeds initial categories, services, vendors, artis, and horoscopes."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding database with Yajaman platform data..."))

        # 1. TAXONOMY / CATEGORIES
        self.stdout.write("1. Seeding categories hierarchy...")
        categories_tree = {
            "Home & Property": [
                "Griha Pravesh", "Vastu Pooja", "Vastu Shanti", "Bhumi Pujan", "Shilanyas Pooja"
            ],
            "Jaap & Anushthan": [
                "Mahamrityunjaya Jaap", "Navgraha Jaap", "Gayatri Jaap", "Shani Jaap", "Other Jaap"
            ],
            "Havan & Yagya": [
                "Ganesh Havan", "Navgraha Havan", "Mahamrityunjaya Havan", "Vastu Havan", "Shanti Havan"
            ],
            "Graha Shanti & Dosha": [
                "Navgraha Shanti", "Shani Shanti", "Mangal Dosha", "Kaal Sarp Dosha", "Pitra Dosha"
            ],
            "Devta Pooja": [
                "Ganesh", "Shiva", "Vishnu", "Lakshmi", "Durga", "Hanuman"
            ],
            "Katha & Path": [
                "Satyanarayan Katha", "Sundarkand", "Durga Saptashati", "Bhagwat Katha", "Ramayan Path"
            ],
            "Family & Sanskar": [
                "Namkaran", "Mundan", "Annaprashan", "Vidyarambh"
            ],
            "Marriage": [
                "Vivah Pooja", "Vivah Badha Nivaran", "Mangal Dosha Nivaran"
            ],
            "Business & Office": [
                "Shop Opening", "Office Opening", "Business Pooja", "Office Vastu"
            ],
            "Vehicle Pooja": [
                "New Vehicle Pooja"
            ],
            "Pitru & Ancestor": [
                "Shraddha", "Tarpan", "Pitra Dosha Nivaran"
            ],
            "Festival Pooja": [
                "Diwali", "Navratri", "Ganesh Chaturthi", "Shivratri", "Janmashtami"
            ],
            # Generic multi-service categories
            "Barber & Grooming": [
                "Haircut & Beard", "Hair Spa", "Kids Haircut"
            ],
            "Spa & Massage": [
                "Ayurvedic Abhyanga", "Deep Tissue Therapy", "Head & Shoulder Reflexology"
            ]
        }

        category_objs = {}
        for idx, (parent_name, subcategories) in enumerate(categories_tree.items(), start=1):
            parent_slug = slugify(parent_name)
            parent_cat, _ = Category.objects.get_or_create(
                slug=parent_slug,
                defaults={
                    'name': parent_name,
                    'display_order': idx,
                    'icon_url': f"https://images.unsplash.com/photo-1609358905590-4822605335e2?w=150&auto=format&fit=crop&q=80",
                    'is_active': True
                }
            )
            category_objs[parent_name] = parent_cat

            for s_idx, sub_name in enumerate(subcategories, start=1):
                sub_slug = slugify(f"{parent_slug}-{sub_name}")
                sub_cat, _ = Category.objects.get_or_create(
                    slug=sub_slug,
                    defaults={
                        'name': sub_name,
                        'parent': parent_cat,
                        'display_order': s_idx,
                        'icon_url': f"https://images.unsplash.com/photo-1544717305-2782549b5136?w=150&auto=format&fit=crop&q=80",
                        'is_active': True
                    }
                )
                category_objs[f"{parent_name}->{sub_name}"] = sub_cat

        self.stdout.write(self.style.SUCCESS(f"Categories seeded: {Category.objects.count()} categories in database."))

        # 2. TAGS
        tag_auspicious, _ = Tag.objects.get_or_create(name="Auspicious", slug="auspicious")
        tag_peace, _ = Tag.objects.get_or_create(name="Peace & Prosperity", slug="peace-prosperity")
        tag_health, _ = Tag.objects.get_or_create(name="Health & Protection", slug="health-protection")

        # 3. SERVICES (POOJA & GENERIC ON-DEMAND SERVICES)
        self.stdout.write("2. Seeding comprehensive services...")
        services_data = [
            {
                "name": "Griha Pravesh Pooja",
                "slug": "griha-pravesh-pooja",
                "category": category_objs["Home & Property->Griha Pravesh"],
                "banner_image_url": "https://images.unsplash.com/photo-1609358905590-4822605335e2?w=1024&auto=format&fit=crop&q=80",
                "thumbnail_url": "https://images.unsplash.com/photo-1609358905590-4822605335e2?w=400&auto=format&fit=crop&q=80",
                "duration_text": "2.5 - 3 Hours",
                "duration_minutes_min": 150,
                "duration_minutes_max": 180,
                "vendors_required": 1,
                "rating_average": 4.9,
                "reviews_count": 142,
                "price_without_samagri": 2500.00,
                "price_with_samagri": 4200.00,
                "about": (
                    "Griha Pravesh is a sacred Vedic ceremony performed before entering a newly constructed or "
                    "purchased home. It dispels negative energies, purifies the premises, and invites the divine blessings "
                    "of Vastu Purusha, Lord Ganesha, and Goddess Lakshmi for prosperity, harmony, and peace."
                ),
                "meta": {
                    "scripture_source": "Vastu Shastra & Matsya Purana",
                    "origin_story": "According to Matsya Purana, when the divine architect Vishwakarma designed dwellings, sages ordained Griha Pravesh with Kalash Sthapana to sanctify the sacred quarters.",
                    "benefits": [
                        {"title": "Spiritual Purification", "description": "Purifies the aura and eliminates negative vibrations in the home.", "icon": "shield"},
                        {"title": "Prosperity & Wealth", "description": "Invokes the eternal grace of Goddess Mahalakshmi.", "icon": "trending_up"},
                        {"title": "Vastu Alignment", "description": "Balances the Pancha Bhutas (five elements) inside the premises.", "icon": "balance"}
                    ]
                },
                "is_popular": True,
                "samagri": [
                    {"item_name": "Pure Desi Cow Ghee", "quantity": "500g"},
                    {"item_name": "Havan Kund Samagri Blend", "quantity": "1 kg"},
                    {"item_name": "Brass Kalash & Nariyal (Coconut)", "quantity": "1 Set"},
                    {"item_name": "Ganga Jal & Panchamrit", "quantity": "1 Bottle"},
                    {"item_name": "Roli, Akshat, Chandan & Janeu", "quantity": "1 Pack"},
                    {"item_name": "Mango Wood for Havan", "quantity": "2 kg"}
                ]
            },
            {
                "name": "Bhumi Pujan",
                "slug": "bhumi-pujan",
                "category": category_objs["Home & Property->Bhumi Pujan"],
                "banner_image_url": "https://images.unsplash.com/photo-1544717305-2782549b5136?w=1024&auto=format&fit=crop&q=80",
                "thumbnail_url": "https://images.unsplash.com/photo-1544717305-2782549b5136?w=400&auto=format&fit=crop&q=80",
                "duration_text": "1.5 - 2 Hours",
                "duration_minutes_min": 90,
                "duration_minutes_max": 120,
                "vendors_required": 1,
                "rating_average": 4.8,
                "reviews_count": 89,
                "price_without_samagri": 2100.00,
                "price_with_samagri": 3600.00,
                "about": "Bhumi Pujan seeks permission and blessings from Mother Earth (Bhumi Devi) and Vastu Purusha before commencing any excavation or construction.",
                "meta": {
                    "scripture_source": "Vishwakarma Prakash",
                    "origin_story": "Sanctioned in ancient architectural sutras to ask forgiveness from Mother Earth for disturbing soil and native life during construction.",
                    "benefits": [
                        {"title": "Smooth Construction", "description": "Protects against delays and accidents on site."},
                        {"title": "Mother Earth's Grace", "description": "Ensures stability and fertile ground for occupants."}
                    ]
                },
                "is_popular": True,
                "samagri": [
                    {"item_name": "Silver Snake (Nag-Nagin joda)", "quantity": "1 pair"},
                    {"item_name": "Navratna & Panchadhatu Coins", "quantity": "1 pack"},
                    {"item_name": "Turmeric, Kumkum & Supari", "quantity": "250g"}
                ]
            },
            {
                "name": "Satyanarayan Katha & Pooja",
                "slug": "satyanarayan-katha",
                "category": category_objs["Katha & Path->Satyanarayan Katha"],
                "banner_image_url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1024&auto=format&fit=crop&q=80",
                "thumbnail_url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=400&auto=format&fit=crop&q=80",
                "duration_text": "2 - 2.5 Hours",
                "duration_minutes_min": 120,
                "duration_minutes_max": 150,
                "vendors_required": 1,
                "rating_average": 4.9,
                "reviews_count": 210,
                "price_without_samagri": 1800.00,
                "price_with_samagri": 2900.00,
                "about": "Lord Satyanarayan is the embodiment of Supreme Truth. Reciting the five chapters of this katha brings auspiciousness, removes obstacles, and fulfills vows.",
                "meta": {
                    "scripture_source": "Skanda Purana, Reva Khanda",
                    "origin_story": "Narrated by Lord Narayana to Sage Narada as the most potent remedy for peace and righteousness in Kali Yuga.",
                    "benefits": [
                        {"title": "Obstacle Removal", "description": "Eliminates unforeseen challenges in career and home life."},
                        {"title": "Family Harmony", "description": "Brings the entire family together in truth and prayer."}
                    ]
                },
                "is_popular": True,
                "samagri": [
                    {"item_name": "Panchamrit & Panjiri Prasad Samagri", "quantity": "1 kg"},
                    {"item_name": "Banana Leaves & Fresh Betel Leaves", "quantity": "5 pieces"},
                    {"item_name": "Tulsi Dal & Yellow Cloth", "quantity": "1 pack"}
                ]
            },
            {
                "name": "Mahamrityunjaya Jaap & Havan",
                "slug": "mahamrityunjaya-jaap",
                "category": category_objs["Jaap & Anushthan->Mahamrityunjaya Jaap"],
                "banner_image_url": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=1024&auto=format&fit=crop&q=80",
                "thumbnail_url": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=400&auto=format&fit=crop&q=80",
                "duration_text": "3 - 4 Hours",
                "duration_minutes_min": 180,
                "duration_minutes_max": 240,
                "vendors_required": 2,
                "rating_average": 5.0,
                "reviews_count": 94,
                "price_without_samagri": 5100.00,
                "price_with_samagri": 7500.00,
                "about": "The Great Death-Conquering Mantra to Lord Shiva bestowed by Rishi Markandeya, bestowing health, longevity, and liberation from chronic illness.",
                "meta": {
                    "scripture_source": "Rigveda & Shiva Purana",
                    "origin_story": "Given to Rishi Markandeya by Lord Shiva to protect against untimely demise.",
                    "benefits": [
                        {"title": "Health & Longevity", "description": "Mitigates acute physical distress and illness."},
                        {"title": "Divine Protection", "description": "Shields against untimely adversities and negative planetary transits."}
                    ]
                },
                "is_popular": True,
                "samagri": [
                    {"item_name": "Bilva Patra & Dhatura", "quantity": "21 leaves"},
                    {"item_name": "Herbal Ayurvedic Jaap Samagri", "quantity": "2 kg"},
                    {"item_name": "Pure Sesame Oil & Ghee", "quantity": "1 kg"}
                ]
            },
            {
                "name": "Namkaran Sanskar (Naming Ceremony)",
                "slug": "namkaran-sanskar",
                "category": category_objs["Family & Sanskar->Namkaran"],
                "banner_image_url": "https://images.unsplash.com/photo-1519741497674-611481863552?w=1024&auto=format&fit=crop&q=80",
                "thumbnail_url": "https://images.unsplash.com/photo-1519741497674-611481863552?w=400&auto=format&fit=crop&q=80",
                "duration_text": "1.5 - 2 Hours",
                "duration_minutes_min": 90,
                "duration_minutes_max": 120,
                "vendors_required": 1,
                "rating_average": 4.9,
                "reviews_count": 115,
                "price_without_samagri": 2100.00,
                "price_with_samagri": 3200.00,
                "about": "One of the primary 16 Vedic Sanskars to calculate auspicious astrological syllable according to Janma Nakshatra and officially name the newborn child.",
                "meta": {
                    "scripture_source": "Grihya Sutras",
                    "origin_story": "Conducted on the 11th or 12th day of birth to initiate the newborn's identity in harmony with the cosmos.",
                    "benefits": [
                        {"title": "Auspicious Syllables", "description": "Calculates name resonance with planetary constellations for lifelong fortune."},
                        {"title": "Divine Blessings", "description": "Infuses long life, intelligence, and moral virtues."}
                    ]
                },
                "is_popular": True,
                "samagri": [
                    {"item_name": "Bronze Thali with Uncooked Rice", "quantity": "1 pack"},
                    {"item_name": "Gold or Silver Needle/Stylus", "quantity": "1 piece"},
                    {"item_name": "Baby Kalash & Honey", "quantity": "1 bottle"}
                ]
            },
            {
                "name": "New Vehicle Pooja (Vahan Pooja)",
                "slug": "new-vehicle-pooja",
                "category": category_objs["Vehicle Pooja->New Vehicle Pooja"],
                "banner_image_url": "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=1024&auto=format&fit=crop&q=80",
                "thumbnail_url": "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=400&auto=format&fit=crop&q=80",
                "duration_text": "30 - 45 Minutes",
                "duration_minutes_min": 30,
                "duration_minutes_max": 45,
                "vendors_required": 1,
                "rating_average": 4.8,
                "reviews_count": 312,
                "price_without_samagri": 501.00,
                "price_with_samagri": 901.00,
                "about": "Protects your new car, bike, or commercial vehicle against road mishaps, malefic sight (Nazar), and ensures safe, peaceful journeys.",
                "meta": {
                    "scripture_source": "Atharva Veda",
                    "origin_story": "Performed to consecrate instruments of travel with Lord Ganesha and Hanumanji's protection.",
                    "benefits": [
                        {"title": "Safe Journeys", "description": "Wards off road hazards and vehicular malfunctions."},
                        {"title": "Evil Eye Protection", "description": "Sanctifies vehicle with Nimbu-Mirchi and sacred Swastika."}
                    ]
                },
                "is_popular": True,
                "samagri": [
                    {"item_name": "4 Green Lemons & Fresh Garland", "quantity": "1 set"},
                    {"item_name": "Red Sindoor & Camphor (Karpuram)", "quantity": "1 pack"},
                    {"item_name": "Coconut (Nariyal) & Mauli Thread", "quantity": "1 set"}
                ]
            },
            # Generic on-demand service (Barber / Grooming)
            {
                "name": "Men's Executive Haircut & Beard Grooming",
                "slug": "mens-executive-haircut-beard",
                "category": category_objs["Barber & Grooming->Haircut & Beard"],
                "banner_image_url": "https://images.unsplash.com/photo-1503951914875-452162b0f3f1?w=1024&auto=format&fit=crop&q=80",
                "thumbnail_url": "https://images.unsplash.com/photo-1503951914875-452162b0f3f1?w=400&auto=format&fit=crop&q=80",
                "duration_text": "45 - 60 Minutes",
                "duration_minutes_min": 45,
                "duration_minutes_max": 60,
                "vendors_required": 1,
                "rating_average": 4.8,
                "reviews_count": 184,
                "price_without_samagri": 499.00,
                "price_with_samagri": 799.00,
                "about": "Professional at-home styling session with sanitized single-use disposables, beard shaping, and revitalizing head massage.",
                "meta": {
                    "service_type": "Grooming",
                    "hygiene_protocol": "100% disposable cape, sterilized blades, skin-safe alcohol wipes.",
                    "benefits": [
                        {"title": "Doorstep Convenience", "description": "Salon quality without queues in the comfort of your home."},
                        {"title": "Sterilized Hygiene", "description": "Fresh single-use blades and tools every time."}
                    ]
                },
                "is_popular": True,
                "samagri": [
                    {"item_name": "Disposable Salon Cape & Neck Strips", "quantity": "1 set"},
                    {"item_name": "Beard Oil & Aftershave Balm", "quantity": "1 kit"}
                ]
            }
        ]

        for s_data in services_data:
            samagri_items = s_data.pop("samagri", [])
            service, _ = Service.objects.update_or_create(
                slug=s_data['slug'],
                defaults=s_data
            )
            service.tags.add(tag_auspicious, tag_peace)

            for item in samagri_items:
                PoojaSamagriItem.objects.update_or_create(
                    service=service,
                    item_name=item['item_name'],
                    defaults={'quantity': item.get('quantity', '1 unit'), 'is_included_by_default': True}
                )

        self.stdout.write(self.style.SUCCESS(f"Services seeded: {Service.objects.count()} services."))

        # 4. VENDORS (PANDITS & STYLISTS)
        self.stdout.write("3. Seeding verified vendors...")
        vendors_data = [
            {
                "name": "Acharya Rameshwar Shastri",
                "phone_number": "+919811122233",
                "email": "shastri.rameshwar@yajaman.in",
                "origin_state": "Uttar Pradesh",
                "origin_city": "Varanasi",
                "qualification": "Acharya in Shukla Yajurveda & Vastu Shastra from Sampurnanand Sanskrit Vishwavidyalaya",
                "experience_years": 16,
                "rating_average": 4.9,
                "reviews_count": 240,
                "current_latitude": 28.6139,
                "current_longitude": 77.2090,
                "service_radius_km": 25.0,
                "category": category_objs["Home & Property"]
            },
            {
                "name": "Pandit Vidyadhar Joshi",
                "phone_number": "+919811144455",
                "email": "joshi.vidyadhar@yajaman.in",
                "origin_state": "Uttarakhand",
                "origin_city": "Haridwar",
                "qualification": "Jyotish Ratna & Vedic Karmakanda Specialist",
                "experience_years": 12,
                "rating_average": 4.8,
                "reviews_count": 180,
                "current_latitude": 28.6304,
                "current_longitude": 77.2177,
                "service_radius_km": 20.0,
                "category": category_objs["Katha & Path"]
            },
            {
                "name": "Pandit Alok Nath Trivedi",
                "phone_number": "+919811166677",
                "email": "alok.trivedi@yajaman.in",
                "origin_state": "Uttar Pradesh",
                "origin_city": "Ayodhya",
                "qualification": "Mahavidya Anushthan & Sanskar Vidhan Expert",
                "experience_years": 9,
                "rating_average": 4.9,
                "reviews_count": 112,
                "current_latitude": 28.5355,
                "current_longitude": 77.3910,
                "service_radius_km": 30.0,
                "category": category_objs["Jaap & Anushthan"]
            },
            {
                "name": "Rohit Verma (Master Stylist)",
                "phone_number": "+919811188899",
                "email": "rohit.stylist@yajaman.in",
                "origin_state": "Delhi",
                "origin_city": "New Delhi",
                "qualification": "L'Oréal Certified Master Barber & Grooming Specialist",
                "experience_years": 8,
                "rating_average": 4.8,
                "reviews_count": 310,
                "current_latitude": 28.5562,
                "current_longitude": 77.1000,
                "service_radius_km": 15.0,
                "category": category_objs["Barber & Grooming"]
            }
        ]

        for v_data in vendors_data:
            cat = v_data.pop("category", None)
            vendor, _ = Vendor.objects.update_or_create(
                phone_number=v_data['phone_number'],
                defaults=v_data
            )
            if cat:
                vendor.categories.add(cat)

            # Assign dummy device token for FCM testing
            VendorDevice.objects.update_or_create(
                vendor=vendor,
                fcm_token=f"fcm_token_vendor_{vendor.phone_number.replace('+', '')}",
                defaults={'device_type': 'android'}
            )

        self.stdout.write(self.style.SUCCESS(f"Vendors seeded: {Vendor.objects.count()} active vendors."))

        # 5. DEVOTIONAL ARTIS (AUDIO + LYRICS)
        self.stdout.write("4. Seeding popular Artis with audio streaming links...")
        artis_data = [
            {
                "title": "Jai Ganesh Deva (Ganesh Ji Ki Aarti)",
                "slug": "jai-ganesh-deva",
                "deity": "Lord Ganesha",
                "duration_seconds": 240,
                "thumbnail_url": "https://images.unsplash.com/photo-1567591414240-e1451f28b335?w=400&auto=format&fit=crop&q=80",
                "audio_url": "https://actions.google.com/sounds/v1/religions/ganesh_arti_sample.mp3",
                "is_popular": True,
                "display_order": 1,
                "lyrics_text": (
                    "जय गणेश, जय गणेश, जय गणेश देवा।\n"
                    "माता जाकी पार्वती, पिता महादेवा॥\n\n"
                    "एकदन्त, दयावन्त, चार भुजाधारी।\n"
                    "माथे सिन्दूर सोहे, मूसे की सवारी॥\n\n"
                    "पान चढ़े, फूल चढ़े और चढ़े मेवा।\n"
                    "लड्डुअन का भोग लगे, सन्त करें सेवा॥\n\n"
                    "अन्धन को आंख देत, कोढ़िन को काया।\n"
                    "बांझन को पुत्र देत, निर्धन को माया॥\n\n"
                    "सूर' श्याम शरण आए, सफल कीजे सेवा।\n"
                    "माता जाकी पार्वती, पिता महादेवा॥"
                )
            },
            {
                "title": "Om Jai Lakshmi Mata (Lakshmi Ji Ki Aarti)",
                "slug": "om-jai-lakshmi-mata",
                "deity": "Goddess Lakshmi",
                "duration_seconds": 280,
                "thumbnail_url": "https://images.unsplash.com/photo-1544717305-2782549b5136?w=400&auto=format&fit=crop&q=80",
                "audio_url": "https://actions.google.com/sounds/v1/religions/lakshmi_arti_sample.mp3",
                "is_popular": True,
                "display_order": 2,
                "lyrics_text": (
                    "ॐ जय लक्ष्मी माता, मैया जय लक्ष्मी माता।\n"
                    "तुमको निसदिन सेवत, हर विष्णु विधाता॥\n\n"
                    "उमा, रमा, ब्रह्माणी, तुम ही जग-माता।\n"
                    "सूर्य-चन्द्रमा ध्यावत, नारद ऋषि गाता॥\n\n"
                    "दुर्गा रूप निरंजनि, सुख सम्पति दाता।\n"
                    "जो कोई तुमको ध्यावत, ऋद्धि-सिद्धि धन पाता॥\n\n"
                    "जिस घर में तुम रहती, सब सद्गुण आता।\n"
                    "सब संभव हो जाता, मन नहिं घबराता॥"
                )
            },
            {
                "title": "Jai Shiv Omkara (Shiva Ji Ki Aarti)",
                "slug": "jai-shiv-omkara",
                "deity": "Lord Shiva",
                "duration_seconds": 270,
                "thumbnail_url": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=400&auto=format&fit=crop&q=80",
                "audio_url": "https://actions.google.com/sounds/v1/religions/shiva_arti_sample.mp3",
                "is_popular": True,
                "display_order": 3,
                "lyrics_text": (
                    "जय शिव ओंकारा, हर ॐ शिव ओंकारा।\n"
                    "ब्रह्मा, विष्णु, सदाशिव, अर्द्धांगी धारा॥\n\n"
                    "एकानन चतुरानन पंचानन राजे।\n"
                    "हंसासन गरुड़ासन वृषवाहन साजे॥\n\n"
                    "दो भुज चार चतुर्भुज दसभुज अति सोहे।\n"
                    "त्रिगुण रूप निरखते त्रिभुवन जन मोहे॥"
                )
            },
            {
                "title": "Shri Hanuman Chalisa",
                "slug": "shri-hanuman-chalisa",
                "deity": "Lord Hanuman",
                "duration_seconds": 540,
                "thumbnail_url": "https://images.unsplash.com/photo-1609358905590-4822605335e2?w=400&auto=format&fit=crop&q=80",
                "audio_url": "https://actions.google.com/sounds/v1/religions/hanuman_chalisa_sample.mp3",
                "is_popular": True,
                "display_order": 4,
                "lyrics_text": (
                    "श्रीगुरु चरन सरोज रज निज मनु मुकुरु सुधारि।\n"
                    "बरनऊं रघुबर बिमल जसु जो दायकु फल चारि॥\n\n"
                    "बुद्धिहीन तनु जानिके, सुमिरौं पवन-कुमार।\n"
                    "बल बुद्धि बिद्या देहु मोहिं, हरहु कलेस बिकार॥\n\n"
                    "जय हनुमान ज्ञान गुन सागर। जय कपीस तिहुं लोक उजागर॥\n"
                    "राम दूत अतुलित बल धामा। अंजनि-पुत्र पवनसुत नामा॥"
                )
            }
        ]

        for a_data in artis_data:
            Arti.objects.update_or_create(slug=a_data['slug'], defaults=a_data)

        self.stdout.write(self.style.SUCCESS(f"Artis seeded: {Arti.objects.count()} devotional artis."))

        # 6. HOROSCOPES (12 ZODIAC SIGNS - TODAY & NEXT MONTH)
        self.stdout.write("5. Seeding Horoscopes for all 12 Zodiac signs...")
        today = datetime.date.today()
        first_of_month = today.replace(day=1)

        zodiacs = [
            ("Aries", "Red", 9, "High energy and initiative today. Professional endeavors receive favorable cosmic alignment."),
            ("Taurus", "White", 6, "Financial clarity emerges. Grounded focus brings peace at home and auspicious family harmony."),
            ("Gemini", "Yellow", 5, "Favorable day for intellectual pursuits and communications. A new opportunity arises."),
            ("Cancer", "Silver", 2, "Intuitive wisdom guides important household decisions. Blessed with emotional contentment."),
            ("Leo", "Gold", 1, "Leadership qualities radiate brightly. Recognition and success in endeavors favored today."),
            ("Virgo", "Green", 5, "Organized workflow brings rapid progress. Auspicious time to begin healthy routines."),
            ("Libra", "Pink", 7, "Harmonious partnerships flourish. Auspicious time for social gatherings and spiritual prayer."),
            ("Scorpio", "Maroon", 8, "Deep determination unlocks long-pending tasks. Spiritual contemplation brings breakthrough."),
            ("Sagittarius", "Orange", 3, "Optimism and learning guide your path. Beneficial journeys and mentorship favored."),
            ("Capricorn", "Blue", 4, "Steadfast discipline delivers enduring rewards. Good news in career or business expansion."),
            ("Aquarius", "Sky Blue", 8, "Innovative solutions emerge effortlessly. Social connections yield positive synergies."),
            ("Pisces", "Purple", 3, "Spiritual clarity and compassionate vibes uplift your day. Devotional worship brings deep peace.")
        ]

        for sign, color, num, daily_text in zodiacs:
            # Daily
            Horoscope.objects.update_or_create(
                zodiac_sign=sign,
                period_type=Horoscope.PeriodType.DAILY,
                period_date=today,
                defaults={
                    "prediction_text": daily_text,
                    "lucky_color": color,
                    "lucky_number": num,
                    "icon_url": f"https://api.iconify.design/game-icons:zodiac-{sign.lower()}.svg"
                }
            )

            # Monthly
            Horoscope.objects.update_or_create(
                zodiac_sign=sign,
                period_type=Horoscope.PeriodType.MONTHLY,
                period_date=first_of_month,
                defaults={
                    "prediction_text": f"Throughout this upcoming month, {sign} natives experience stability, growth in wealth, and renewed spiritual focus.",
                    "lucky_color": color,
                    "lucky_number": num,
                    "icon_url": f"https://api.iconify.design/game-icons:zodiac-{sign.lower()}.svg"
                }
            )

        self.stdout.write(self.style.SUCCESS(f"Horoscopes seeded: {Horoscope.objects.count()} horoscope records."))

        # 7. DEMO USER & DEFAULT ADDRESS
        self.stdout.write("6. Seeding demo customer and address...")
        demo_user, _ = User.objects.get_or_create(
            phone_number="+919876543210",
            defaults={
                "full_name": "Amit Sharma",
                "email": "amit.sharma@example.com",
                "phone_verified_at": timezone.now(),
                "origin_state": "Uttar Pradesh",
                "origin_city": "Varanasi",
                "gotra": "Kashyap",
                "mother_tongue": "hi"
            }
        )
        # Device
        UserDevice.objects.update_or_create(
            user=demo_user,
            fcm_token="fcm_token_demo_customer_amit",
            defaults={"device_type": "react_native_android"}
        )

        # Addresses
        addr1, _ = UserAddress.objects.update_or_create(
            user=demo_user,
            custom_title="My Home",
            defaults={
                "address_type": UserAddress.AddressType.HOME,
                "flat_house_building": "Tower B, Apt 502, Shivalik Residency",
                "street_area_locality": "Sector 62",
                "city": "Noida",
                "state": "Uttar Pradesh",
                "postal_code": "201309",
                "landmark": "Near Fortis Hospital",
                "latitude": 28.6200,
                "longitude": 77.3600,
                "is_default": True
            }
        )

        UserAddress.objects.update_or_create(
            user=demo_user,
            custom_title="Office",
            defaults={
                "address_type": UserAddress.AddressType.OFFICE,
                "flat_house_building": "DLF Cyber City, 8th Floor",
                "street_area_locality": "Phase 2",
                "city": "Gurugram",
                "state": "Haryana",
                "postal_code": "122002",
                "latitude": 28.4900,
                "longitude": 77.0900,
                "is_default": False
            }
        )

        self.stdout.write(self.style.SUCCESS("Demo customer and addresses seeded successfully!"))
        self.stdout.write(self.style.SUCCESS("All seed data successfully generated!"))
