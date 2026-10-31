from django.db import migrations

POSTGIS_FUNCTION_SQL = """
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
LANGUAGE plpgsql
AS $$
DECLARE
    curr_radius numeric := p_initial_radius;
    cust_point geography := ST_SetSRID(ST_MakePoint(p_cust_lon, p_cust_lat), 4326)::geography;
    has_matches boolean := false;
BEGIN
    WHILE curr_radius <= p_max_radius LOOP
        -- Check if any candidate vendors match all constraints within curr_radius
        SELECT EXISTS (
            SELECT 1
            FROM vendors v
            WHERE v.is_active = true
              AND v.is_available = true
              AND v.is_on_duty = true
              AND v.current_latitude IS NOT NULL
              AND v.current_longitude IS NOT NULL
              AND (
                  p_category_ids IS NULL 
                  OR NOT EXISTS (SELECT 1 FROM vendor_categories vc_all WHERE vc_all.vendor_id = v.id)
                  OR EXISTS (SELECT 1 FROM vendor_categories vc WHERE vc.vendor_id = v.id AND vc.category_id = ANY(p_category_ids))
              )
              AND ST_DWithin(
                  ST_SetSRID(ST_MakePoint(v.current_longitude, v.current_latitude), 4326)::geography,
                  cust_point,
                  LEAST(curr_radius, COALESCE(v.service_radius_km, 15.0)) * 1000.0
              )
        ) INTO has_matches;

        IF has_matches THEN
            RETURN QUERY
            SELECT 
                v.id AS vendor_id,
                v.name,
                v.phone_number,
                v.origin_state,
                v.origin_city,
                v.rating_average,
                ROUND((ST_Distance(
                    ST_SetSRID(ST_MakePoint(v.current_longitude, v.current_latitude), 4326)::geography,
                    cust_point
                ) / 1000.0)::numeric, 2) AS distance_km,
                (CASE 
                    WHEN LOWER(TRIM(COALESCE(p_user_state, ''))) <> '' 
                         AND LOWER(TRIM(COALESCE(v.origin_state, ''))) = LOWER(TRIM(p_user_state)) THEN 
                        CASE 
                            WHEN LOWER(TRIM(COALESCE(p_user_city, ''))) <> '' 
                                 AND LOWER(TRIM(COALESCE(v.origin_city, ''))) = LOWER(TRIM(p_user_city)) THEN 100
                            ELSE 50 
                        END
                    ELSE 0 
                END)::integer AS priority_score
            FROM vendors v
            WHERE v.is_active = true
              AND v.is_available = true
              AND v.is_on_duty = true
              AND v.current_latitude IS NOT NULL
              AND v.current_longitude IS NOT NULL
              AND (
                  p_category_ids IS NULL 
                  OR NOT EXISTS (SELECT 1 FROM vendor_categories vc_all WHERE vc_all.vendor_id = v.id)
                  OR EXISTS (SELECT 1 FROM vendor_categories vc WHERE vc.vendor_id = v.id AND vc.category_id = ANY(p_category_ids))
              )
              AND ST_DWithin(
                  ST_SetSRID(ST_MakePoint(v.current_longitude, v.current_latitude), 4326)::geography,
                  cust_point,
                  LEAST(curr_radius, COALESCE(v.service_radius_km, 15.0)) * 1000.0
              )
            ORDER BY 
                priority_score DESC,
                distance_km ASC,
                v.rating_average DESC;
            RETURN;
        END IF;

        IF curr_radius >= p_max_radius THEN
            EXIT;
        END IF;

        curr_radius := LEAST(curr_radius + p_step_km, p_max_radius);
    END LOOP;

    RETURN;
END;
$$;
"""

def create_postgis_objects(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_vendors_postgis_geog 
            ON vendors USING GIST (CAST(ST_SetSRID(ST_MakePoint(current_longitude, current_latitude), 4326) AS geography));
        """)
        cursor.execute(POSTGIS_FUNCTION_SQL)

def drop_postgis_objects(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("DROP FUNCTION IF EXISTS find_eligible_vendors_postgis(numeric, numeric, uuid[], text, text, numeric, numeric, numeric);")
        cursor.execute("DROP INDEX IF EXISTS idx_vendors_postgis_geog;")

class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0003_vendor_location_updated_at_vendorlocationhistory'),
    ]

    operations = [
        migrations.RunPython(create_postgis_objects, drop_postgis_objects),
    ]
