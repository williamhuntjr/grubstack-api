CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;
COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';

CREATE TABLE public.gs_tenant (
    tenant_id uuid DEFAULT public.uuid_generate_v4() PRIMARY KEY NOT NULL,
    is_suspended boolean DEFAULT false,
    is_active boolean DEFAULT true,
    slug character varying(12) NOT NULL,
    access_token character varying(16) NOT NULL
);
ALTER TABLE public.gs_tenant OWNER TO grubstack;

CREATE TABLE public.gs_log (
    tenant_id UUID NOT NULL REFERENCES gs_tenant (tenant_id) ON DELETE RESTRICT,
    log_id SERIAL PRIMARY KEY NOT NULL,
    log_created timestamp with time zone,
    log_asctime text,
    log_name text,
    log_loglevel integer,
    log_loglevelname text,
    log_message text,
    log_args text,
    log_module text,
    log_funcname text,
    log_lineno integer,
    log_exception text,
    log_process integer,
    log_thread text,
    log_threadname text
);
ALTER TABLE public.gs_log OWNER TO grubstack;


CREATE TABLE public.gs_permission (
    permission_id SERIAL PRIMARY KEY NOT NULL,
    name character varying(64) NOT NULL,
    description character varying(255)
);
ALTER TABLE public.gs_permission OWNER TO grubstack;


CREATE TABLE public.gs_user_permission (
    tenant_id UUID NOT NULL REFERENCES gs_tenant (tenant_id) ON DELETE RESTRICT,
    user_id text NOT NULL,
    permission_id integer NOT NULL
);
ALTER TABLE public.gs_user_permission OWNER TO grubstack;


CREATE TABLE public.gs_role (
    role_id SERIAL PRIMARY KEY NOT NULL,
    name character varying(64) NOT NULL,
    descripion character varying(255)
);
ALTER TABLE public.gs_role OWNER TO grubstack;


CREATE TABLE public.gs_user_role (
    tenant_id UUID NOT NULL REFERENCES gs_tenant (tenant_id) ON DELETE RESTRICT,
    user_id text NOT NULL,
    role_id integer NOT NULL
);
ALTER TABLE public.gs_user_role OWNER TO grubstack;

                                                                                                                               
CREATE TABLE public.gs_store ( 
    tenant_id UUID NOT NULL REFERENCES gs_tenant (tenant_id) ON DELETE RESTRICT,                                                                                                
    store_id SERIAL PRIMARY KEY NOT NULL,                                                                                                 
    name character varying(64) NOT NULL,                                                                                                                 
    address1 character varying(255) NOT NULL,                                                                                                             
    city character varying(64) NOT NULL,                                                                                                
    state character varying(64) NOT NULL,                                                                                               
    postal character varying(32) NOT NULL,                                                                                              
    store_type character varying(32) NOT NULL,                                                                                                           
    thumbnail_url text,
    phone_number character varying(32) NOT NULL                                                                                                        
);                                                                                                                             
ALTER TABLE public.gs_store OWNER TO grubstack;                                                                                


CREATE TABLE public.gs_ingredient (
    tenant_id UUID NOT NULL REFERENCES gs_tenant (tenant_id) ON DELETE RESTRICT,                                                                                                
    ingredient_id SERIAL PRIMARY KEY NOT NULL,
    name character varying(255) NOT NULL,
    description character varying(255),
    thumbnail_url text,
    calories double precision DEFAULT 0.0,
    fat double precision DEFAULT 0.0,
    saturated_fat double precision DEFAULT 0.0,
    trans_fat double precision DEFAULT 0.0,
    cholesterol double precision DEFAULT 0.0,
    sodium double precision DEFAULT 0.0,
    carbs double precision DEFAULT 0.0,
    protein double precision DEFAULT 0.0,
    sugar double precision DEFAULT 0.0,
    fiber double precision DEFAULT 0.0,
    price double precision DEFAULT 0.0
);
ALTER TABLE public.gs_ingredient OWNER TO grubstack;


CREATE TABLE public.gs_menu (
    tenant_id UUID NOT NULL REFERENCES gs_tenant (tenant_id) ON DELETE RESTRICT,                                                                                                
    menu_id SERIAL PRIMARY KEY NOT NULL,
    name character varying(255) NOT NULL,
    description character varying(255),
    thumbnail_url text
);
ALTER TABLE public.gs_menu OWNER TO grubstack;


CREATE TABLE public.gs_menu_item (
    tenant_id UUID NOT NULL REFERENCES gs_tenant (tenant_id) ON DELETE RESTRICT,                                                                                                
    menu_id integer NOT NULL,
    item_id integer NOT NULL,
    price double precision DEFAULT 0.0,
    sale_price double precision DEFAULT 0.0,
    is_onsale boolean
);
ALTER TABLE public.gs_menu_item OWNER TO grubstack;


CREATE TABLE public.gs_item (
    tenant_id UUID NOT NULL REFERENCES gs_tenant (tenant_id) ON DELETE RESTRICT,                                                                                                
    item_id SERIAL PRIMARY KEY NOT NULL,
    name character varying(255) NOT NULL,
    description character varying(255),
    thumbnail_url text
);
ALTER TABLE public.gs_item OWNER TO grubstack;


CREATE TABLE public.gs_item_ingredient (
    tenant_id UUID NOT NULL REFERENCES gs_tenant (tenant_id) ON DELETE RESTRICT,                                                                                                
    item_id integer NOT NULL,
    ingredient_id integer NOT NULL,
    is_optional boolean,
    is_addon boolean,
    is_extra boolean
);
ALTER TABLE public.gs_item_ingredient OWNER TO grubstack;


CREATE TABLE public.gs_item_variety (
    tenant_id UUID NOT NULL REFERENCES gs_tenant (tenant_id) ON DELETE RESTRICT,                                                                                                
    item_id integer NOT NULL,
    variety_id integer NOT NULL
);
ALTER TABLE public.gs_item_variety OWNER TO grubstack;


CREATE TABLE public.gs_variety (
    tenant_id UUID NOT NULL REFERENCES gs_tenant (tenant_id) ON DELETE RESTRICT,                                                                                                
    variety_id SERIAL PRIMARY KEY NOT NULL,
    name character varying(255) NOT NULL,
    description character varying(255),
    thumbnail_url text
);
ALTER TABLE public.gs_variety OWNER TO grubstack;


CREATE TABLE public.gs_variety_ingredient (
    tenant_id UUID NOT NULL REFERENCES gs_tenant (tenant_id) ON DELETE RESTRICT,                                                                                                
    variety_id integer NOT NULL,
    ingredient_id integer NOT NULL
);
ALTER TABLE public.gs_variety_ingredient OWNER TO grubstack;


CREATE TABLE public.gs_media_library (
    tenant_id UUID NOT NULL REFERENCES gs_tenant (tenant_id) ON DELETE RESTRICT,                                                                                                
    file_id SERIAL PRIMARY KEY NOT NULL, 
    file_name TEXT NOT NULL, 
    file_size BIGINT NOT NULL, 
    file_type character varying(64) NOT NULL
);
ALTER TABLE public.gs_media_library OWNER TO grubstack;


CREATE TABLE public.gs_employee (
    tenant_id UUID NOT NULL REFERENCES gs_tenant (tenant_id) ON DELETE RESTRICT,
    employee_id SERIAL PRIMARY KEY NOT NULL,                                                                                             
    first_name character varying(64) NOT NULL,
    last_name character varying(64) NOT NULL,
    gender character varying(16) NOT NULL,
    address1 TEXT NOT NULL,
    city character varying(64) NOT NULL,
    state character varying(64) NOT NULL,
    postal character varying(32) NOT NULL,
    phone character varying(32),
    email character varying(255),
    profile_thumbnail_url TEXT,
    hire_date DATE,
    employment_status character varying(16),
    job_title character varying(64) NOT NULL
);
ALTER TABLE public.gs_employee OWNER TO grubstack;

CREATE TABLE public.gs_store_employee (
    tenant_id UUID NOT NULL REFERENCES gs_tenant (tenant_id) ON DELETE RESTRICT,                                                                                                
    store_id integer NOT NULL,
    employee_id integer NOT NULL
);
ALTER TABLE public.gs_store_employee OWNER TO grubstack;

CREATE TABLE public.gs_store_menu (
    tenant_id UUID NOT NULL REFERENCES gs_tenant (tenant_id) ON DELETE RESTRICT,
    store_id integer NOT NULL,
    menu_id integer NOT NULL
);
ALTER TABLE public.gs_store_menu OWNER TO grubstack;

ALTER TABLE gs_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE gs_user_role ENABLE ROW LEVEL SECURITY;
ALTER TABLE gs_user_permission ENABLE ROW LEVEL SECURITY;
ALTER TABLE gs_store ENABLE ROW LEVEL SECURITY;
ALTER TABLE gs_ingredient ENABLE ROW LEVEL SECURITY;
ALTER TABLE gs_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE gs_menu ENABLE ROW LEVEL SECURITY;
ALTER TABLE gs_menu_item ENABLE ROW LEVEL SECURITY;
ALTER TABLE gs_item ENABLE ROW LEVEL SECURITY;
ALTER TABLE gs_item_ingredient ENABLE ROW LEVEL SECURITY;
ALTER TABLE gs_item_variety ENABLE ROW LEVEL SECURITY;
ALTER TABLE gs_variety ENABLE ROW LEVEL SECURITY;
ALTER TABLE gs_variety_ingredient ENABLE ROW LEVEL SECURITY;
ALTER TABLE gs_media_library ENABLE ROW LEVEL SECURITY;
ALTER TABLE gs_employee ENABLE ROW LEVEL SECURITY;
ALTER TABLE gs_store_employee ENABLE ROW LEVEL SECURITY;
ALTER TABLE gs_store_menu ENABLE ROW LEVEL SECURITY;

ALTER TABLE gs_log FORCE ROW LEVEL SECURITY;
ALTER TABLE gs_user_role FORCE ROW LEVEL SECURITY;
ALTER TABLE gs_user_permission FORCE ROW LEVEL SECURITY;
ALTER TABLE gs_store FORCE ROW LEVEL SECURITY;
ALTER TABLE gs_ingredient FORCE ROW LEVEL SECURITY;
ALTER TABLE gs_log FORCE ROW LEVEL SECURITY;
ALTER TABLE gs_menu FORCE ROW LEVEL SECURITY;
ALTER TABLE gs_menu_item FORCE ROW LEVEL SECURITY;
ALTER TABLE gs_item FORCE ROW LEVEL SECURITY;
ALTER TABLE gs_item_ingredient FORCE ROW LEVEL SECURITY;
ALTER TABLE gs_item_variety FORCE ROW LEVEL SECURITY;
ALTER TABLE gs_variety FORCE ROW LEVEL SECURITY;
ALTER TABLE gs_variety_ingredient FORCE ROW LEVEL SECURITY;
ALTER TABLE gs_media_library FORCE ROW LEVEL SECURITY;
ALTER TABLE gs_employee FORCE ROW LEVEL SECURITY;
ALTER TABLE gs_store_employee FORCE ROW LEVEL SECURITY;
ALTER TABLE gs_store_menu FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_policy ON gs_log USING (tenant_id = current_setting('app.tenant_id')::UUID);
CREATE POLICY tenant_isolation_policy ON gs_user_role USING (tenant_id = current_setting('app.tenant_id')::UUID);
CREATE POLICY tenant_isolation_policy ON gs_user_permission USING (tenant_id = current_setting('app.tenant_id')::UUID);
CREATE POLICY tenant_isolation_policy ON gs_store USING (tenant_id = current_setting('app.tenant_id')::UUID);
CREATE POLICY tenant_isolation_policy ON gs_ingredient USING (tenant_id = current_setting('app.tenant_id')::UUID);
CREATE POLICY tenant_isolation_policy ON gs_menu USING (tenant_id = current_setting('app.tenant_id')::UUID);
CREATE POLICY tenant_isolation_policy ON gs_menu_item USING (tenant_id = current_setting('app.tenant_id')::UUID);
CREATE POLICY tenant_isolation_policy ON gs_item USING (tenant_id = current_setting('app.tenant_id')::UUID);
CREATE POLICY tenant_isolation_policy ON gs_item_ingredient USING (tenant_id = current_setting('app.tenant_id')::UUID);
CREATE POLICY tenant_isolation_policy ON gs_item_variety USING (tenant_id = current_setting('app.tenant_id')::UUID);
CREATE POLICY tenant_isolation_policy ON gs_variety USING (tenant_id = current_setting('app.tenant_id')::UUID);
CREATE POLICY tenant_isolation_policy ON gs_variety_ingredient USING (tenant_id = current_setting('app.tenant_id')::UUID);
CREATE POLICY tenant_isolation_policy ON gs_media_library USING (tenant_id = current_setting('app.tenant_id')::UUID);
CREATE POLICY tenant_isolation_policy ON gs_employee USING (tenant_id = current_setting('app.tenant_id')::UUID);
CREATE POLICY tenant_isolation_policy ON gs_store_employee USING (tenant_id = current_setting('app.tenant_id')::UUID);
CREATE POLICY tenant_isolation_policy ON gs_store_menu USING (tenant_id = current_setting('app.tenant_id')::UUID);

INSERT INTO gs_permission VALUES (1, 'ViewStores', 'Allow user to view stores');
INSERT INTO gs_permission VALUES (2, 'MaintainStores', 'Allow user to to add, delete, and update stores');
INSERT INTO gs_permission VALUES (3, 'ViewMenus', 'Allow user to view menus');
INSERT INTO gs_permission VALUES (4, 'MaintainMenus', 'Allow user to to add, delete, and update menus');
INSERT INTO gs_permission VALUES (5, 'ViewItems', 'Allow user to view items');
INSERT INTO gs_permission VALUES (6, 'MaintainItems', 'Allow user to to add, delete, and update items');
INSERT INTO gs_permission VALUES (7, 'ViewIngredients', 'Allow user to view ingredients');
INSERT INTO gs_permission VALUES (8, 'MaintainIngredients', 'Allow user to to add, delete, and update ingredients');
INSERT INTO gs_permission VALUES (9, 'ViewVarieties', 'Allow user to view varieties');
INSERT INTO gs_permission VALUES (10, 'MaintainVarieties', 'Allow user to to add, delete, and update varieties');
INSERT INTO gs_permission VALUES (11, 'ViewMediaLibrary', 'Allow user to view media library files');
INSERT INTO gs_permission VALUES (12, 'MaintainMediaLibrary', 'Allow user to to add, delete, and update media library files');
INSERT INTO gs_permission VALUES (13, 'ViewEmployees', 'Allow user to view employees');
INSERT INTO gs_permission VALUES (14, 'MaintainEmployees', 'Allow user to to add, delete, and update employees');

INSERT INTO gs_role VALUES (1, 'Administrator', 'Provides full access to the dashboard');
INSERT INTO gs_role VALUES (2, 'Employee', 'Provides read-only access to dashboard');
