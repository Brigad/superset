CREATE OR REPLACE FUNCTION set_roles_dashboard() RETURNS trigger
   LANGUAGE plpgsql AS
$$
DECLARE
	dash_role record;
BEGIN 
   IF TG_WHEN != 'AFTER' OR TG_LEVEL != 'ROW' THEN
    RAISE TRIGGER_PROTOCOL_VIOLATED USING
    MESSAGE = 'function "set_roles" must be fired AFTER ROW';
  END IF;

  IF TG_OP != 'INSERT' THEN
    RAISE TRIGGER_PROTOCOL_VIOLATED USING
    MESSAGE = 'function "set_roles" must be fired for INSERT only';
  END IF;
  
  IF TG_TABLE_NAME != 'dashboards' THEN
  	RAISE TRIGGER_PROTOCOL_VIOLATED USING
    MESSAGE = 'function "set_roles" must be fired for dashboards only';
  END IF;
  
  for dash_role in select id FROM ab_role WHERE name IN ('Admin', 'Viewer', 'Editor')
  loop
  	EXECUTE ('INSERT INTO dashboard_roles(role_id, dashboard_id) VALUES (' || dash_role.id || ', ' || NEW.id || ')');
  end loop;
  
  RETURN NEW;
END;
$$;

CREATE OR REPLACE TRIGGER set_dashboard_roles_on_insert AFTER INSERT ON dashboards FOR EACH ROW EXECUTE FUNCTION set_roles_dashboard();