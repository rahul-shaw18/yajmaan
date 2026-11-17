from django.utils import timezone
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import Vendor, VendorOnboardingApplication, VendorDevice, VendorLocationHistory
from apps.accounts.models import User
from .serializers import (
    VendorPublicProfileSerializer,
    VendorOnboardingApplicationSerializer,
    VendorDeviceSerializer,
    VendorLocationUpdateSerializer,
    VendorLocationResponseSerializer,
    VendorDutyToggleSerializer
)



class VendorOnboardingView(generics.CreateAPIView):
    queryset = VendorOnboardingApplication.objects.all()
    serializer_class = VendorOnboardingApplicationSerializer
    permission_classes = [AllowAny]


class VendorListView(generics.ListAPIView):
    queryset = Vendor.objects.filter(is_active=True, is_available=True)
    serializer_class = VendorPublicProfileSerializer
    permission_classes = [AllowAny]


class VendorDetailView(generics.RetrieveAPIView):
    queryset = Vendor.objects.filter(is_active=True)
    serializer_class = VendorPublicProfileSerializer
    lookup_field = 'id'
    permission_classes = [AllowAny]


class VendorDeviceView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=VendorDeviceSerializer,
        responses={200: VendorDeviceSerializer},
        description="Register or update vendor FCM push notification device token."
    )
    def post(self, request):
        serializer = VendorDeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device = serializer.save()
        return Response(VendorDeviceSerializer(device).data, status=status.HTTP_200_OK)


class VendorLocationView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=VendorLocationUpdateSerializer,
        responses={
            200: VendorLocationResponseSerializer,
            400: OpenApiResponse(description="Vendor is not on duty or invalid coordinates provided"),
            404: OpenApiResponse(description="Vendor not found")
        },
        description="Update vendor's live GPS coordinates (e.g. every 30 minutes from vendor device). Only allowed when vendor is on duty."
    )
    def post(self, request):
        return self._update_location(request)

    @extend_schema(
        request=VendorLocationUpdateSerializer,
        responses={
            200: VendorLocationResponseSerializer,
            400: OpenApiResponse(description="Vendor is not on duty or invalid coordinates provided"),
            404: OpenApiResponse(description="Vendor not found")
        },
        description="Update vendor's live GPS coordinates (e.g. every 30 minutes from vendor device). Only allowed when vendor is on duty."
    )
    def patch(self, request):
        return self._update_location(request)

    def _update_location(self, request):
        serializer = VendorLocationUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vendor_id = serializer.validated_data['vendor_id']
        lat = serializer.validated_data['latitude']
        lon = serializer.validated_data['longitude']

        try:
            vendor = Vendor.objects.get(id=vendor_id)
        except Vendor.DoesNotExist:
            return Response(
                {"error": "NOT_FOUND", "detail": "Vendor not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # On-Duty Validation: Only allow location updates if vendor is currently on duty!
        if not vendor.is_on_duty:
            return Response(
                {
                    "error": "VENDOR_OFF_DUTY",
                    "detail": "Vendor is currently off duty. Location updates can only be saved when vendor is on duty.",
                    "is_on_duty": False,
                    "vendor_id": str(vendor.id)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        now = timezone.now()
        vendor.current_latitude = lat
        vendor.current_longitude = lon
        vendor.location_updated_at = now
        vendor.save(update_fields=['current_latitude', 'current_longitude', 'location_updated_at', 'updated_at'])

        # Record 30-minute periodic heartbeat in location history table
        VendorLocationHistory.objects.create(
            vendor=vendor,
            latitude=lat,
            longitude=lon
        )

        return Response({
            "status": "success",
            "message": "Vendor location recorded successfully.",
            "vendor_id": str(vendor.id),
            "current_latitude": float(vendor.current_latitude),
            "current_longitude": float(vendor.current_longitude),
            "location_updated_at": vendor.location_updated_at.isoformat(),
            "is_on_duty": vendor.is_on_duty
        }, status=status.HTTP_200_OK)


class VendorAvailableJobsView(APIView):
    """
    Returns jobs currently dispatched to this vendor that are still waiting to be accepted.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        responses={200: OpenApiResponse(description="Returns active dispatched bookings for vendor")},
        description="List active dispatched booking requests for a specific vendor."
    )
    def get(self, request):
        vendor_id = request.query_params.get('vendor_id')
        if not vendor_id:
            return Response({"detail": "vendor_id query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            vendor = Vendor.objects.get(id=vendor_id)
        except Vendor.DoesNotExist:
            return Response({"detail": "Vendor not found."}, status=status.HTTP_404_NOT_FOUND)

        from apps.bookings.models import BookingDispatchLog, Booking
        from apps.bookings.serializers import BookingListSerializer

        # Find bookings dispatched to this vendor where response_status is DISPATCHED and booking is still SEARCHING_VENDOR or REQUESTED
        active_dispatches = BookingDispatchLog.objects.filter(
            vendor=vendor,
            response_status='DISPATCHED',
            booking__status__in=[Booking.BookingStatus.REQUESTED, Booking.BookingStatus.SEARCHING_VENDOR]
        ).select_related('booking', 'booking__service', 'booking__user', 'booking__address')

        bookings = [log.booking for log in active_dispatches]
        serializer = BookingListSerializer(bookings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class VendorDutyView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=VendorDutyToggleSerializer,
        responses={200: VendorPublicProfileSerializer},
        description="Toggle vendor onDuty status ON or OFF."
    )
    def patch(self, request):
        serializer = VendorDutyToggleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vendor_id = serializer.validated_data['vendor_id']
        is_on_duty = serializer.validated_data['is_on_duty']

        try:
            vendor = Vendor.objects.get(id=vendor_id)
        except Vendor.DoesNotExist:
            return Response({"detail": "Vendor not found."}, status=status.HTTP_404_NOT_FOUND)

        vendor.is_on_duty = is_on_duty
        vendor.save(update_fields=['is_on_duty', 'updated_at'])

        return Response(VendorPublicProfileSerializer(vendor).data, status=status.HTTP_200_OK)


class VendorAssignmentsView(APIView):
    """
    Returns assignments (upcoming confirmed poojas and pending dispatched requests) for a vendor.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        responses={200: OpenApiResponse(description="Returns upcoming and pending assignments for vendor")},
        description="Retrieve upcoming assignments for the vendor dashboard."
    )
    def get(self, request):
        from apps.bookings.models import Booking, BookingDispatchLog

        vendor = None
        vendor_id = request.query_params.get('vendor_id')

        if vendor_id:
            try:
                vendor = Vendor.objects.filter(id=vendor_id).first()
            except Exception:
                pass

        if not vendor and request.user.is_authenticated:
            vendor = Vendor.objects.filter(phone_number=getattr(request.user, 'phone_number', '')).first()

        if not vendor:
            vendor = Vendor.objects.filter(is_active=True).first()

        results = []

        if vendor:
            # 1. Confirmed / In Progress Bookings assigned to this vendor
            assigned_bookings = Booking.objects.filter(
                vendor=vendor,
                status__in=[Booking.BookingStatus.ACCEPTED, Booking.BookingStatus.IN_PROGRESS]
            ).select_related('service', 'user', 'address').order_by('preferred_date', 'preferred_time_slot')

            for b in assigned_bookings:
                loc = "Customer Location"
                if isinstance(b.snapshot_booking_address, dict):
                    loc = b.snapshot_booking_address.get('formatted_address') or b.snapshot_booking_address.get('city') or loc
                elif b.address:
                    loc = b.address.formatted_address

                customer_name = "Yajmaan"
                if b.user:
                    customer_name = b.user.get_full_name() or b.user.phone_number

                results.append({
                    "id": str(b.id),
                    "title": b.service.name if b.service else "Vedic Pooja",
                    "customer": customer_name,
                    "date": b.preferred_date.strftime("%d %b %Y") if b.preferred_date else "Today",
                    "time": b.preferred_time_slot or "10:00 AM",
                    "location": loc,
                    "status": "confirmed",
                    "payout": float(b.total_price) if b.total_price else 1500
                })

            # 2. Dispatched bookings waiting for acceptance
            pending_dispatches = BookingDispatchLog.objects.filter(
                vendor=vendor,
                response_status='DISPATCHED',
                booking__status__in=[Booking.BookingStatus.REQUESTED, Booking.BookingStatus.SEARCHING_VENDOR]
            ).select_related('booking', 'booking__service', 'booking__user', 'booking__address')

            for log in pending_dispatches:
                b = log.booking
                loc = "Customer Location"
                if isinstance(b.snapshot_booking_address, dict):
                    loc = b.snapshot_booking_address.get('formatted_address') or b.snapshot_booking_address.get('city') or loc
                elif b.address:
                    loc = b.address.formatted_address

                customer_name = "Yajmaan"
                if b.user:
                    customer_name = b.user.get_full_name() or b.user.phone_number

                results.append({
                    "id": str(b.id),
                    "title": b.service.name if b.service else "Vedic Pooja",
                    "customer": customer_name,
                    "date": b.preferred_date.strftime("%d %b %Y") if b.preferred_date else "Today",
                    "time": b.preferred_time_slot or "10:00 AM",
                    "location": loc,
                    "status": "pending_acceptance",
                    "payout": float(b.total_price) if b.total_price else 1500
                })

        # 3. Fallback demo data if no bookings in DB yet
        if not results:
            results = [
                {
                    "id": "JOB-101",
                    "title": "Satyanarayan Pooja",
                    "customer": "Rahul Kumar",
                    "date": "Today",
                    "time": "10:00 AM",
                    "location": "Sector 4, Dwarka",
                    "status": "pending_acceptance",
                    "payout": 1500
                },
                {
                    "id": "JOB-102",
                    "title": "Griha Pravesh",
                    "customer": "Amit Singh",
                    "date": "Tomorrow",
                    "time": "08:00 AM",
                    "location": "Vasant Kunj",
                    "status": "confirmed",
                    "payout": 4000
                }
            ]

        return Response(results, status=status.HTTP_200_OK)


class VendorOnboardingStatusView(APIView):
    """
    Checks whether the vendor is onboarded, in draft, pending approval, or rejected.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        phone = request.query_params.get('phone')
        if not phone and request.user.is_authenticated:
            phone = getattr(request.user, 'phone_number', '')

        if not phone:
            return Response(
                {"detail": "phone parameter is required or user must be authenticated"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Look up vendor and linked application
        vendor = Vendor.objects.filter(phone_number=phone).first()
        application = None
        if vendor and vendor.onboarding_application:
            application = vendor.onboarding_application
        else:
            application = VendorOnboardingApplication.objects.filter(phone_number=phone).order_by('-updated_at', '-created_at').first()

        if not application:
            return Response({
                "is_onboarded": False,
                "status": "NOT_STARTED",
                "step": 1,
                "application": None,
                "vendor": VendorPublicProfileSerializer(vendor).data if vendor else None
            }, status=status.HTTP_200_OK)

        # 1. If application is PENDING_APPROVAL:
        if application.status == VendorOnboardingApplication.Status.PENDING_APPROVAL:
            return Response({
                "is_onboarded": False,
                "status": "PENDING_APPROVAL",
                "step": application.step_completed or 5,
                "rejection_reason": None,
                "application": VendorOnboardingApplicationSerializer(application).data,
                "vendor": VendorPublicProfileSerializer(vendor).data if vendor else None
            }, status=status.HTTP_200_OK)

        # 2. If application is REJECTED:
        if application.status == VendorOnboardingApplication.Status.REJECTED:
            return Response({
                "is_onboarded": False,
                "status": "REJECTED",
                "step": application.step_completed or 1,
                "rejection_reason": application.rejection_reason,
                "application": VendorOnboardingApplicationSerializer(application).data,
                "vendor": VendorPublicProfileSerializer(vendor).data if vendor else None
            }, status=status.HTTP_200_OK)

        # 3. If application is APPROVED:
        if application.status == VendorOnboardingApplication.Status.APPROVED:
            if vendor and not vendor.is_active:
                vendor.is_active = True
                vendor.save(update_fields=['is_active'])
            return Response({
                "is_onboarded": True,
                "status": "APPROVED",
                "vendor": VendorPublicProfileSerializer(vendor).data if vendor else None,
                "application": VendorOnboardingApplicationSerializer(application).data
            }, status=status.HTTP_200_OK)

        # 4. Fallback (e.g. DRAFT):
        return Response({
            "is_onboarded": False,
            "status": application.status,
            "step": application.step_completed or 1,
            "rejection_reason": application.rejection_reason,
            "application": VendorOnboardingApplicationSerializer(application).data,
            "vendor": VendorPublicProfileSerializer(vendor).data if vendor else None
        }, status=status.HTTP_200_OK)


class VendorOnboardingDraftView(APIView):
    """
    Saves partial progress of the multi-step vendor onboarding form.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        phone = request.data.get('phone_number')
        if not phone and request.user.is_authenticated:
            phone = getattr(request.user, 'phone_number', '')

        if not phone:
            return Response(
                {"detail": "phone_number is required to save progress"},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = request.data.copy()
        data['phone_number'] = phone
        step = data.get('step_completed', 1)

        application = VendorOnboardingApplication.objects.filter(phone_number=phone).order_by('-created_at').first()
        if application and application.status != VendorOnboardingApplication.Status.APPROVED:
            serializer = VendorOnboardingApplicationSerializer(application, data=data, partial=True)
        else:
            serializer = VendorOnboardingApplicationSerializer(data=data, partial=True)

        if serializer.is_valid():
            app_obj = serializer.save(status=VendorOnboardingApplication.Status.DRAFT, step_completed=step)
            return Response({
                "status": "DRAFT",
                "step": app_obj.step_completed,
                "message": "Draft progress saved successfully.",
                "application": VendorOnboardingApplicationSerializer(app_obj).data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VendorOnboardingSubmitView(APIView):
    """
    Submits completed onboarding application for admin approval.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        phone = request.data.get('phone_number')
        if not phone and request.user.is_authenticated:
            phone = getattr(request.user, 'phone_number', '')

        if not phone:
            return Response(
                {"detail": "phone_number is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        application = VendorOnboardingApplication.objects.filter(phone_number=phone).order_by('-created_at').first()
        if not application:
            serializer = VendorOnboardingApplicationSerializer(data=request.data)
        else:
            serializer = VendorOnboardingApplicationSerializer(application, data=request.data, partial=True)

        if serializer.is_valid():
            app_obj = serializer.save(
                status=VendorOnboardingApplication.Status.PENDING_APPROVAL,
                reviewed_at=None,
                rejection_reason=None
            )
            vendor = Vendor.objects.filter(phone_number=phone).first()
            if not vendor:
                vendor = Vendor.objects.create(
                    phone_number=phone,
                    name=app_obj.full_name or 'Pandit Ji',
                    is_active=False,
                    onboarding_application=app_obj
                )
            else:
                vendor.onboarding_application = app_obj
                if app_obj.full_name:
                    vendor.name = app_obj.full_name
                vendor.save(update_fields=['onboarding_application', 'name'])

            return Response({
                "status": "PENDING_APPROVAL",
                "message": "Application submitted successfully and is pending admin approval.",
                "application": VendorOnboardingApplicationSerializer(app_obj).data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VendorAdminApplicationsView(generics.ListAPIView):
    """
    Lists vendor onboarding applications for admin panel review.
    """
    permission_classes = [AllowAny]
    serializer_class = VendorOnboardingApplicationSerializer
    pagination_class = None

    def get_queryset(self):
        status_filter = self.request.query_params.get('status')
        qs = VendorOnboardingApplication.objects.all().order_by('-updated_at', '-created_at')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class VendorAdminAcceptView(APIView):
    """
    Admin accepts vendor onboarding application. Creates/activates Vendor profile.
    """
    permission_classes = [AllowAny]

    def post(self, request, id):
        try:
            application = VendorOnboardingApplication.objects.get(id=id)
        except VendorOnboardingApplication.DoesNotExist:
            return Response({"detail": "Application not found."}, status=status.HTTP_404_NOT_FOUND)

        application.status = VendorOnboardingApplication.Status.APPROVED
        application.reviewed_at = timezone.now()
        application.rejection_reason = None
        application.save()

        # Create or update Vendor record
        vendor, created = Vendor.objects.update_or_create(
            phone_number=application.phone_number,
            defaults={
                'name': application.full_name,
                'email': application.email,
                'origin_state': application.origin_state,
                'origin_city': application.origin_city,
                'qualification': application.qualification,
                'experience_years': application.experience_years or 5,
                'specializations': application.specializations,
                'address': application.address,
                'home_latitude': application.home_latitude,
                'home_longitude': application.home_longitude,
                'onboarding_application': application,
                'is_active': True,
                'is_available': True,
            }
        )

        return Response({
            "status": "success",
            "message": f"Vendor '{vendor.name}' has been successfully approved.",
            "application": VendorOnboardingApplicationSerializer(application).data,
            "vendor": VendorPublicProfileSerializer(vendor).data
        }, status=status.HTTP_200_OK)


class VendorAdminRejectView(APIView):
    """
    Admin rejects vendor onboarding application with an optional reason.
    """
    permission_classes = [AllowAny]

    def post(self, request, id):
        try:
            application = VendorOnboardingApplication.objects.get(id=id)
        except VendorOnboardingApplication.DoesNotExist:
            return Response({"detail": "Application not found."}, status=status.HTTP_404_NOT_FOUND)

        reason = request.data.get('reason', 'Application rejected by administrator')
        application.status = VendorOnboardingApplication.Status.REJECTED
        application.rejection_reason = reason
        application.reviewed_at = timezone.now()
        application.save()

        # Deactivate any active vendor profile
        Vendor.objects.filter(phone_number=application.phone_number).update(is_active=False)

        return Response({
            "status": "success",
            "message": "Vendor application rejected.",
            "application": VendorOnboardingApplicationSerializer(application).data
        }, status=status.HTTP_200_OK)


def delete_pandit_account_full(vendor=None, application=None, phone_number=None):
    """
    Safely and permanently deletes Pandit/Vendor records, onboarding applications,
    device tokens, location history, and auth accounts.
    """
    if not phone_number:
        if vendor and vendor.phone_number:
            phone_number = vendor.phone_number
        elif application and application.phone_number:
            phone_number = application.phone_number

    deleted_info = {
        "phone_number": phone_number,
        "vendor_deleted": False,
        "application_deleted": False,
        "user_auth_deleted": False
    }

    if not vendor and phone_number:
        vendor = Vendor.objects.filter(phone_number=phone_number).first()

    if vendor:
        vendor.devices.all().delete()
        vendor.location_history.all().delete()
        vendor.onboarding_application = None
        vendor.save(update_fields=['onboarding_application'])
        vendor.delete()
        deleted_info["vendor_deleted"] = True

    if phone_number:
        cnt, _ = VendorOnboardingApplication.objects.filter(phone_number=phone_number).delete()
        if cnt > 0:
            deleted_info["application_deleted"] = True
    elif application:
        application.delete()
        deleted_info["application_deleted"] = True

    if phone_number:
        for u in User.objects.filter(phone_number=phone_number):
            if hasattr(u, 'bookings'):
                u.bookings.all().delete()
            if hasattr(u, 'addresses'):
                u.addresses.all().delete()
            if hasattr(u, 'devices'):
                u.devices.all().delete()
            if hasattr(u, 'phone_otps'):
                u.phone_otps.all().delete()
            u.delete()
            deleted_info["user_auth_deleted"] = True

    return deleted_info


class VendorAdminListView(APIView):
    """
    List all Pandits/Vendors for the admin control panel.
    Combines active vendors and onboarding applications so admin can manage/delete any account.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        seen_phones = set()
        data = []

        vendors = Vendor.objects.all().order_by('-created_at')
        for v in vendors:
            seen_phones.add(v.phone_number)
            app = v.onboarding_application or VendorOnboardingApplication.objects.filter(phone_number=v.phone_number).order_by('-created_at').first()
            data.append({
                "id": str(v.id),
                "vendor_id": str(v.id),
                "application_id": str(app.id) if app else None,
                "name": v.name or (app.full_name if app else "Pandit Ji"),
                "phone_number": v.phone_number,
                "email": v.email or (app.email if app else "") or "",
                "city": v.origin_city or (app.origin_city if app else "") or "",
                "state": v.origin_state or (app.origin_state if app else "") or "",
                "address": v.address or (app.address if app else "") or "",
                "home_latitude": float(v.home_latitude) if v.home_latitude is not None else (float(app.home_latitude) if app and app.home_latitude is not None else None),
                "home_longitude": float(v.home_longitude) if v.home_longitude is not None else (float(app.home_longitude) if app and app.home_longitude is not None else None),
                "qualification": v.qualification or (app.qualification if app else "") or "",
                "experience_years": v.experience_years,
                "specializations": v.specializations or (app.specializations if app else "") or "",
                "id_proof_type": app.id_proof_type if app else "AADHAAR",
                "id_proof_number": app.id_proof_number if app else "",
                "id_proof_document_url": app.id_proof_document_url if app else "",
                "pan_card_number": app.pan_card_number if app else "",
                "pan_card_document_url": app.pan_card_document_url if app else "",
                "bank_account_number": app.bank_account_number if app else "",
                "bank_ifsc_code": app.bank_ifsc_code if app else "",
                "bank_beneficiary_name": app.bank_beneficiary_name if app else "",
                "rating_average": float(v.rating_average),
                "is_active": v.is_active,
                "is_available": v.is_available,
                "is_on_duty": v.is_on_duty,
                "status": app.status if app else ("APPROVED" if v.is_active else "PENDING_APPROVAL"),
                "rejection_reason": app.rejection_reason if app else None,
                "created_at": v.created_at,
            })

        apps = VendorOnboardingApplication.objects.exclude(phone_number__in=seen_phones).order_by('-created_at')
        for a in apps:
            data.append({
                "id": str(a.id),
                "vendor_id": None,
                "application_id": str(a.id),
                "name": a.full_name or "Pt. Applicant",
                "phone_number": a.phone_number,
                "email": a.email or "",
                "city": a.origin_city or "",
                "state": a.origin_state or "",
                "address": a.address or "",
                "home_latitude": float(a.home_latitude) if a.home_latitude is not None else None,
                "home_longitude": float(a.home_longitude) if a.home_longitude is not None else None,
                "qualification": a.qualification or "",
                "experience_years": a.experience_years,
                "specializations": a.specializations or "",
                "id_proof_type": a.id_proof_type or "AADHAAR",
                "id_proof_number": a.id_proof_number or "",
                "id_proof_document_url": a.id_proof_document_url or "",
                "pan_card_number": a.pan_card_number or "",
                "pan_card_document_url": a.pan_card_document_url or "",
                "bank_account_number": a.bank_account_number or "",
                "bank_ifsc_code": a.bank_ifsc_code or "",
                "bank_beneficiary_name": a.bank_beneficiary_name or "",
                "rating_average": 5.0,
                "is_active": False,
                "is_available": False,
                "is_on_duty": False,
                "status": a.status,
                "rejection_reason": a.rejection_reason,
                "created_at": a.created_at,
            })

        return Response(data, status=status.HTTP_200_OK)


class VendorAdminDeleteVendorView(APIView):
    """
    Permanently delete a Pandit / Vendor account and all associated applications/auth records.
    """
    permission_classes = [AllowAny]

    def delete(self, request, id):
        vendor = Vendor.objects.filter(id=id).first()
        if not vendor:
            app = VendorOnboardingApplication.objects.filter(id=id).first()
            if not app:
                return Response({"detail": "Pandit account not found."}, status=status.HTTP_404_NOT_FOUND)
            phone = app.phone_number
            name = app.full_name or "Pandit Ji"
            delete_pandit_account_full(application=app, phone_number=phone)
            return Response({
                "status": "success",
                "message": f"Pandit application for '{name}' ({phone}) permanently deleted."
            }, status=status.HTTP_200_OK)

        phone = vendor.phone_number
        name = vendor.name or "Pandit Ji"
        delete_pandit_account_full(vendor=vendor, phone_number=phone)

        return Response({
            "status": "success",
            "message": f"Pandit profile for '{name}' ({phone}) permanently deleted."
        }, status=status.HTTP_200_OK)

    def post(self, request, id):
        return self.delete(request, id)


class VendorAdminDeleteApplicationView(APIView):
    """
    Permanently delete an onboarding application and associated vendor/auth account if any.
    """
    permission_classes = [AllowAny]

    def delete(self, request, id):
        app = VendorOnboardingApplication.objects.filter(id=id).first()
        if not app:
            vendor = Vendor.objects.filter(id=id).first()
            if not vendor:
                return Response({"detail": "Application not found."}, status=status.HTTP_404_NOT_FOUND)
            phone = vendor.phone_number
            name = vendor.name or "Pandit Ji"
            delete_pandit_account_full(vendor=vendor, phone_number=phone)
            return Response({
                "status": "success",
                "message": f"Pandit profile for '{name}' ({phone}) permanently deleted."
            }, status=status.HTTP_200_OK)

        phone = app.phone_number
        name = app.full_name or "Pt. Applicant"
        delete_pandit_account_full(application=app, phone_number=phone)

        return Response({
            "status": "success",
            "message": f"Application for '{name}' ({phone}) permanently deleted."
        }, status=status.HTTP_200_OK)

    def post(self, request, id):
        return self.delete(request, id)


class VendorMeView(APIView):
    """
    View and edit current vendor's profile, including name, address, current location, home location.
    """
    permission_classes = [AllowAny]

    def _get_vendor(self, request):
        vendor_id = request.query_params.get('vendor_id') or request.data.get('vendor_id')
        if vendor_id:
            v = Vendor.objects.filter(id=vendor_id).first()
            if v:
                return v

        phone = request.query_params.get('phone') or request.data.get('phone_number')
        if not phone and request.user.is_authenticated:
            phone = getattr(request.user, 'phone_number', '')

        if phone:
            v = Vendor.objects.filter(phone_number=phone).first()
            if not v:
                app = VendorOnboardingApplication.objects.filter(phone_number=phone).order_by('-created_at').first()
                v, _ = Vendor.objects.get_or_create(
                    phone_number=phone,
                    defaults={
                        'name': app.full_name if app and app.full_name else 'Pandit Ji',
                        'is_active': False,
                        'onboarding_application': app
                    }
                )
            if v and not v.onboarding_application:
                app = VendorOnboardingApplication.objects.filter(phone_number=v.phone_number).order_by('-created_at').first()
                if not app:
                    app = VendorOnboardingApplication.objects.create(
                        phone_number=v.phone_number,
                        full_name=v.name or 'Pandit Ji',
                        origin_city=v.origin_city or '',
                        origin_state=v.origin_state or 'Uttar Pradesh',
                        email=v.email or '',
                        qualification=v.qualification or '',
                        experience_years=v.experience_years or 5,
                        specializations=v.specializations or '',
                        address=v.address or '',
                        home_latitude=v.home_latitude,
                        home_longitude=v.home_longitude,
                    )
                v.onboarding_application = app
                v.save(update_fields=['onboarding_application'])
            return v

        v = Vendor.objects.filter(is_active=True).first()
        if v and not v.onboarding_application:
            app = VendorOnboardingApplication.objects.filter(phone_number=v.phone_number).order_by('-created_at').first()
            if not app:
                app = VendorOnboardingApplication.objects.create(
                    phone_number=v.phone_number,
                    full_name=v.name or 'Pandit Ji',
                )
            v.onboarding_application = app
            v.save(update_fields=['onboarding_application'])
        return v

    def get(self, request):
        vendor = self._get_vendor(request)
        if not vendor:
            return Response({"detail": "Vendor profile not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(VendorPublicProfileSerializer(vendor).data, status=status.HTTP_200_OK)

    def patch(self, request):
        vendor = self._get_vendor(request)
        if not vendor:
            return Response({"detail": "Vendor profile not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = VendorPublicProfileSerializer(vendor, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()

            # Also update linked onboarding application for KYC and Bank fields
            app = vendor.onboarding_application
            if not app:
                app = VendorOnboardingApplication.objects.filter(phone_number=vendor.phone_number).order_by('-created_at').first()
                if not app:
                    app = VendorOnboardingApplication.objects.create(
                        phone_number=vendor.phone_number,
                        full_name=vendor.name or 'Pandit Ji',
                    )
                vendor.onboarding_application = app
                vendor.save(update_fields=['onboarding_application'])

            app_fields = [
                'id_proof_type', 'id_proof_number', 'id_proof_document_url',
                'pan_card_number', 'pan_card_document_url',
                'bank_account_number', 'bank_ifsc_code', 'bank_beneficiary_name',
                'qualification', 'experience_years', 'specializations', 'address',
                'home_latitude', 'home_longitude', 'email', 'origin_city', 'origin_state'
            ]
            updated_app = False
            for field in app_fields:
                if field in request.data and request.data[field] is not None:
                    val = request.data[field]
                    if field in ['home_latitude', 'home_longitude'] and val != '':
                        try:
                            val = round(float(val), 6)
                        except (ValueError, TypeError):
                            pass
                    setattr(app, field, val)
                    updated_app = True
            if 'name' in request.data and request.data['name']:
                app.full_name = request.data['name']
                updated_app = True

            # Any profile update automatically sends application for admin verification
            app.status = VendorOnboardingApplication.Status.PENDING_APPROVAL
            app.rejection_reason = None
            app.save()

            # Deactivate vendor until admin reviews and verifies updated profile
            vendor.is_active = False
            vendor.save(update_fields=['is_active', 'updated_at'])
            vendor.refresh_from_db()

            return Response({
                "status": "success",
                "message": "Profile updated successfully and submitted for admin verification.",
                "verification_status": "PENDING_APPROVAL",
                "vendor": VendorPublicProfileSerializer(vendor).data,
                "application": VendorOnboardingApplicationSerializer(app).data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        return self.patch(request)


from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.conf import settings
import os
import uuid
import base64

class VendorDocumentUploadView(APIView):
    """
    Uploads a KYC document (Aadhaar, Voter ID, Passport, PAN Card) for a vendor.
    Saves the file to MEDIA_ROOT/kyc_documents/ and returns the accessible URL.
    """
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        file_obj = request.FILES.get('file') or request.FILES.get('document')
        document_type = request.data.get('document_type', 'id_proof')
        phone = request.data.get('phone_number') or request.data.get('phone')
        data_url = request.data.get('data_url')

        if not file_obj and not data_url:
            return Response({"detail": "No file or document data was provided."}, status=status.HTTP_400_BAD_REQUEST)

        kyc_dir = settings.MEDIA_ROOT / 'kyc_documents'
        os.makedirs(kyc_dir, exist_ok=True)

        if file_obj:
            ext = os.path.splitext(file_obj.name)[1].lower()
            if not ext or ext not in ['.jpg', '.jpeg', '.png', '.webp', '.pdf']:
                ext = '.jpg'
            filename = f"{document_type}_{uuid.uuid4().hex[:10]}{ext}"
            file_path = kyc_dir / filename
            with open(file_path, 'wb+') as dest:
                for chunk in file_obj.chunks():
                    dest.write(chunk)

            relative_url = f"{settings.MEDIA_URL}kyc_documents/{filename}"
            full_url = request.build_absolute_uri(relative_url)

            if phone:
                app = VendorOnboardingApplication.objects.filter(phone_number=phone).order_by('-updated_at', '-created_at').first()
                if app:
                    if document_type in ['id_proof', 'aadhaar', 'voter_id', 'passport', 'id']:
                        app.id_proof_document_url = full_url
                    elif document_type in ['pan', 'pan_card']:
                        app.pan_card_document_url = full_url
                    app.save()

            return Response({
                "status": "success",
                "message": "Document uploaded successfully",
                "url": full_url,
                "relative_url": relative_url,
                "filename": filename
            }, status=status.HTTP_200_OK)

        elif data_url:
            try:
                if ';base64,' in data_url:
                    header, encoded = data_url.split(';base64,')
                    file_bytes = base64.b64decode(encoded)
                    ext = '.jpg'
                    if 'png' in header: ext = '.png'
                    elif 'pdf' in header: ext = '.pdf'
                    elif 'webp' in header: ext = '.webp'
                else:
                    file_bytes = base64.b64decode(data_url)
                    ext = '.jpg'

                filename = f"{document_type}_{uuid.uuid4().hex[:10]}{ext}"
                file_path = kyc_dir / filename
                with open(file_path, 'wb') as f:
                    f.write(file_bytes)

                relative_url = f"{settings.MEDIA_URL}kyc_documents/{filename}"
                full_url = request.build_absolute_uri(relative_url)

                if phone:
                    app = VendorOnboardingApplication.objects.filter(phone_number=phone).order_by('-updated_at', '-created_at').first()
                    if app:
                        if document_type in ['id_proof', 'aadhaar', 'voter_id', 'passport', 'id']:
                            app.id_proof_document_url = full_url
                        elif document_type in ['pan', 'pan_card']:
                            app.pan_card_document_url = full_url
                        app.save()

                return Response({
                    "status": "success",
                    "message": "Document uploaded successfully",
                    "url": full_url,
                    "relative_url": relative_url,
                    "filename": filename
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"detail": f"Failed to process document data: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)



