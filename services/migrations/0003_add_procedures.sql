--
-- Find customer service credentials by ip address.
--
DROP FUNCTION IF EXISTS find_customer_service_by_ip(inet);
CREATE OR REPLACE FUNCTION find_customer_service_by_ip(
  v_customer_ip inet
)
  RETURNS services
  LANGUAGE plpgsql
AS $$
DECLARE
  t_res_row RECORD;
BEGIN

  if v_customer_ip is not null then
    select services.* into t_res_row
    from services
      left join customer_service on (customer_service.service_id = services.id)
      left join customers on (customers.current_service_id = customer_service.id)
      left join networks_ip_leases nil on (nil.customer_id = customers.baseaccount_ptr_id)
      left join base_accounts on (base_accounts.id = customers.baseaccount_ptr_id)
    where nil.ip_address = v_customer_ip and base_accounts.is_active
    limit 1;
    return t_res_row;
  end if;

end
$$;