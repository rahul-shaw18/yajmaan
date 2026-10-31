## Table `django_migrations`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `app` | `varchar` |  |
| `name` | `varchar` |  |
| `applied` | `timestamptz` |  |

## Table `django_content_type`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int4` | Primary Identity |
| `app_label` | `varchar` |  |
| `model` | `varchar` |  |

## Table `auth_permission`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int4` | Primary Identity |
| `name` | `varchar` |  |
| `content_type_id` | `int4` |  |
| `codename` | `varchar` |  |

## Table `auth_group`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int4` | Primary Identity |
| `name` | `varchar` |  Unique |

## Table `auth_group_permissions`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `group_id` | `int4` |  |
| `permission_id` | `int4` |  |

## Table `users`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `password` | `varchar` |  |
| `last_login` | `timestamptz` |  Nullable |
| `is_superuser` | `bool` |  |
| `id` | `uuid` | Primary |
| `full_name` | `varchar` |  |
| `email` | `varchar` |  Nullable Unique |
| `email_verified_at` | `timestamptz` |  Nullable |
| `phone_number` | `varchar` |  Unique |
| `phone_verified_at` | `timestamptz` |  Nullable |
| `avatar_url` | `varchar` |  Nullable |
| `origin_state` | `varchar` |  Nullable |
| `origin_city` | `varchar` |  Nullable |
| `gotra` | `varchar` |  Nullable |
| `mother_tongue` | `varchar` |  |
| `is_active` | `bool` |  |
| `is_staff` | `bool` |  |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |

## Table `users_groups`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `user_id` | `uuid` |  |
| `group_id` | `int4` |  |

## Table `users_user_permissions`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `user_id` | `uuid` |  |
| `permission_id` | `int4` |  |

## Table `phone_auth_otps`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `phone_number` | `varchar` |  |
| `otp_hash` | `varchar` |  |
| `attempts_count` | `int2` |  |
| `expires_at` | `timestamptz` |  |
| `is_verified` | `bool` |  |
| `created_at` | `timestamptz` |  |

## Table `user_phone_update_otps`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `new_phone_number` | `varchar` |  |
| `otp_hash` | `varchar` |  |
| `attempts_count` | `int2` |  |
| `expires_at` | `timestamptz` |  |
| `is_verified` | `bool` |  |
| `created_at` | `timestamptz` |  |
| `user_id` | `uuid` |  |

## Table `user_addresses`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `address_type` | `varchar` |  |
| `custom_title` | `varchar` |  Nullable |
| `flat_house_building` | `varchar` |  |
| `street_area_locality` | `varchar` |  |
| `city` | `varchar` |  |
| `state` | `varchar` |  |
| `postal_code` | `varchar` |  |
| `landmark` | `varchar` |  Nullable |
| `latitude` | `numeric` |  Nullable |
| `longitude` | `numeric` |  Nullable |
| `is_default` | `bool` |  |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |
| `user_id` | `uuid` |  |

## Table `user_devices`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `fcm_token` | `varchar` |  |
| `device_type` | `varchar` |  Nullable |
| `updated_at` | `timestamptz` |  |
| `user_id` | `uuid` |  |

## Table `django_admin_log`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int4` | Primary Identity |
| `action_time` | `timestamptz` |  |
| `object_id` | `text` |  Nullable |
| `object_repr` | `varchar` |  |
| `action_flag` | `int2` |  |
| `change_message` | `text` |  |
| `content_type_id` | `int4` |  Nullable |
| `user_id` | `uuid` |  |

## Table `categories`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `name` | `varchar` |  |
| `slug` | `varchar` |  Unique |
| `icon_url` | `varchar` |  Nullable |
| `display_order` | `int4` |  |
| `is_active` | `bool` |  |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |
| `parent_id` | `uuid` |  Nullable |

## Table `tags`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `name` | `varchar` |  Unique |
| `slug` | `varchar` |  Unique |

## Table `services`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `name` | `varchar` |  |
| `slug` | `varchar` |  Unique |
| `banner_image_url` | `varchar` |  |
| `thumbnail_url` | `varchar` |  Nullable |
| `duration_text` | `varchar` |  |
| `duration_minutes_min` | `int4` |  |
| `duration_minutes_max` | `int4` |  |
| `vendors_required` | `int4` |  |
| `rating_average` | `numeric` |  |
| `reviews_count` | `int4` |  |
| `about` | `text` |  |
| `price_without_samagri` | `numeric` |  |
| `price_with_samagri` | `numeric` |  |
| `meta` | `jsonb` |  |
| `is_popular` | `bool` |  |
| `is_active` | `bool` |  |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |
| `category_id` | `uuid` |  |

## Table `service_tags`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `service_id` | `uuid` |  |
| `tag_id` | `uuid` |  |

## Table `pooja_samagri_items`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `item_name` | `varchar` |  |
| `quantity` | `varchar` |  Nullable |
| `is_included_by_default` | `bool` |  |
| `service_id` | `uuid` |  |

## Table `vendor_onboarding_applications`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `full_name` | `varchar` |  |
| `phone_number` | `varchar` |  |
| `email` | `varchar` |  Nullable |
| `origin_state` | `varchar` |  Nullable |
| `origin_city` | `varchar` |  Nullable |
| `qualification` | `text` |  Nullable |
| `id_proof_type` | `varchar` |  Nullable |
| `id_proof_number` | `varchar` |  Nullable |
| `id_proof_document_url` | `varchar` |  Nullable |
| `pan_card_number` | `varchar` |  Nullable |
| `pan_card_document_url` | `varchar` |  Nullable |
| `bank_account_number` | `varchar` |  Nullable |
| `bank_ifsc_code` | `varchar` |  Nullable |
| `bank_beneficiary_name` | `varchar` |  Nullable |
| `status` | `varchar` |  |
| `rejection_reason` | `text` |  Nullable |
| `created_at` | `timestamptz` |  |
| `reviewed_at` | `timestamptz` |  Nullable |

## Table `vendors`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `name` | `varchar` |  |
| `phone_number` | `varchar` |  Unique |
| `email` | `varchar` |  Nullable Unique |
| `origin_state` | `varchar` |  Nullable |
| `origin_city` | `varchar` |  Nullable |
| `qualification` | `text` |  Nullable |
| `experience_years` | `int2` |  |
| `rating_average` | `numeric` |  |
| `reviews_count` | `int4` |  |
| `current_latitude` | `numeric` |  Nullable |
| `current_longitude` | `numeric` |  Nullable |
| `location_updated_at` | `timestamptz` |  Nullable (Latest 30-min heartbeat timestamp) |
| `service_radius_km` | `numeric` |  |
| `is_active` | `bool` |  |
| `is_available` | `bool` |  |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |
| `onboarding_application_id` | `uuid` |  Nullable Unique |
| `is_on_duty` | `bool` |  |

> **Spatial Index:** `idx_vendors_postgis_geog` on `CAST(ST_SetSRID(ST_MakePoint(current_longitude, current_latitude), 4326) AS geography)` USING GIST.

## Table `vendor_location_history`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `vendor_id` | `uuid` | Foreign Key -> `vendors.id` |
| `latitude` | `numeric` |  |
| `longitude` | `numeric` |  |
| `created_at` | `timestamptz` |  |

## Table `vendor_categories`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `vendor_id` | `uuid` |  |
| `category_id` | `uuid` |  |

## Table `vendor_devices`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `fcm_token` | `varchar` |  |
| `device_type` | `varchar` |  Nullable |
| `updated_at` | `timestamptz` |  |
| `vendor_id` | `uuid` |  |

## Table `bookings`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `pricing_variant` | `varchar` |  |
| `total_price` | `numeric` |  |
| `preferred_date` | `date` |  |
| `preferred_time_slot` | `varchar` |  |
| `snapshot_booking_address` | `jsonb` |  |
| `snapshot_user_spiritual_origin` | `jsonb` |  Nullable |
| `status` | `varchar` |  |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |
| `address_id` | `uuid` |  |
| `service_id` | `uuid` |  |
| `user_id` | `uuid` |  |
| `vendor_id` | `uuid` |  Nullable |

## Table `payments`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `amount` | `numeric` |  |
| `payment_mode` | `varchar` |  |
| `status` | `varchar` |  |
| `transaction_id` | `varchar` |  Nullable |
| `gateway_response` | `jsonb` |  |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |
| `booking_id` | `uuid` |  |

## Table `booking_dispatch_logs`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `fcm_message_id` | `varchar` |  Nullable |
| `response_status` | `varchar` |  |
| `created_at` | `timestamptz` |  |
| `booking_id` | `uuid` |  |
| `vendor_id` | `uuid` |  |

## Table `artis`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `title` | `varchar` |  |
| `slug` | `varchar` |  Unique |
| `deity` | `varchar` |  Nullable |
| `lyrics_text` | `text` |  |
| `audio_url` | `varchar` |  Nullable |
| `duration_seconds` | `int4` |  Nullable |
| `thumbnail_url` | `varchar` |  Nullable |
| `is_popular` | `bool` |  |
| `display_order` | `int4` |  |
| `created_at` | `timestamptz` |  |

## Table `horoscopes`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `zodiac_sign` | `varchar` |  |
| `period_type` | `varchar` |  |
| `period_date` | `date` |  |
| `prediction_text` | `text` |  |
| `lucky_color` | `varchar` |  Nullable |
| `lucky_number` | `int2` |  Nullable |
| `icon_url` | `varchar` |  Nullable |
| `created_at` | `timestamptz` |  |

## Table `django_session`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `session_key` | `varchar` | Primary |
| `session_data` | `text` |  |
| `expire_date` | `timestamptz` |  |

---

## Supabase PostGIS Functions & Stored Procedures

### Function `find_eligible_vendors_postgis`

Finds and ranks all eligible vendors within a dynamic step-wise radius expansion using PostGIS geodesic calculations (`ST_DWithin`, `ST_Distance`).

```sql
CREATE OR REPLACE FUNCTION find_eligible_vendors_postgis(
    p_cust_lat numeric,
    p_cust_lon numeric,
    p_category_ids uuid[] DEFAULT NULL,
    p_user_state text DEFAULT '',
    p_user_city text DEFAULT '',
    p_initial_radius numeric DEFAULT 5.0,
    p_step_km numeric DEFAULT 2.0,
    p_max_radius numeric DEFAULT 10.0
)
RETURNS TABLE (
    vendor_id uuid,
    name varchar,
    phone_number varchar,
    origin_state varchar,
    origin_city varchar,
    rating_average numeric,
    distance_km numeric,
    priority_score integer
)
```

**Features:**
- Uses GiST spatial index `idx_vendors_postgis_geog` on `geography(Point, 4326)` for instant lookups.
- Matches active, available, and on-duty (`is_on_duty = true`) vendors.
- Matches service category (or unassigned all-round vendors).
- Expands radius dynamically: 5 km -> 7 km -> 9 km -> 10 km.
- Computes origin state (+50) and city (+50) spiritual priority matches.
- Sorts by priority score DESC, distance ASC, and rating DESC.


