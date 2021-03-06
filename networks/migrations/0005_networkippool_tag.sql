--
-- Function that find free ip for new lease
--
--
-- Пробуем найти свободный ip из пула адресов. Если не находит то возвращается null.
-- Берём диапазон ip из пула от networks_ip_pool.ip_start до networks_ip_pool.ip_end
-- параллельно берём записи из networks_ip_leases о занятых ip, берём их отсортированными
-- по ip_address. И, по идее, при итерации ip совпадают, когда сгенерированный ip из подести
-- пула меньше ip из занятых то это значит что ip из пула уже удалился, и мы нашли свободный.
--
DROP FUNCTION IF EXISTS find_new_ip_pool_lease( integer, boolean );
CREATE OR REPLACE FUNCTION find_new_ip_pool_lease(
  v_pool_id    integer,
  v_is_dynamic boolean,
  v_tag        varchar(32)
)
  RETURNS inet
LANGUAGE plpgsql
AS $$
DECLARE
  t_ip_iter        inet;
  t_ip_lease       inet;
  t_net_ippool_tbl RECORD;
  t_leases_curs    REFCURSOR;
BEGIN

  -- Ищем текущий пул
  select
    id,
    network,
    ip_start,
    ip_end
  into t_net_ippool_tbl
  from networks_ip_pool
  where id = v_pool_id and is_dynamic = v_is_dynamic
  limit 1
  for update skip locked;

  if not FOUND
  then
    return null;
  end if;

  -- Берём курсор по существующим лизам для текущего пула
  -- и где лизы ещё не просрочены
  open t_leases_curs no scroll for select ip_address
                                   from networks_ip_leases
                                   where
                                     pool_id = t_net_ippool_tbl.id and
                                     ip_address >= t_net_ippool_tbl.ip_start and
                                     ip_address <<= t_net_ippool_tbl.network
                                   order by ip_address
                                   for update skip locked;

  t_ip_iter := t_net_ippool_tbl.ip_start;

  while true loop

    fetch t_leases_curs into t_ip_lease;
    if not FOUND
    then
      -- не нашли лизу, возвращаем текущий ip из подсети
      -- raise notice 'lease not found, return current ip %', t_ip_iter;
      return t_ip_iter;
    end if;

    -- если текущий ip больше или равен максимальному допустимому ip то всё, не нашли свободный ip
    if t_ip_iter >= t_net_ippool_tbl.ip_end
    then
      -- raise notice 'current ip is more than max allowable % -%, end', t_ip_iter, t_net_ippool_tbl.ip_end;
      return null;
    end if;

    -- если текущий ip меньше начального допустимого ip
    if t_ip_iter < t_net_ippool_tbl.ip_start
    then
      -- raise notice 'current ip is less than minimum. go next % - %', t_ip_iter, t_net_ippool_tbl.ip_start;
      t_ip_iter := t_ip_iter + 1;
      continue;
    end if;

    if t_ip_iter = t_ip_lease
    then
      -- сгенерированный ip и занятый из лизов совпадают, дальше
      -- raise notice 'current ip and lease ip is exact, next % - %', t_ip_iter, t_ip_lease;
      t_ip_iter := t_ip_iter + 1;
      continue;
    end if;

    -- Если текущий ip меньше текущего из пула то значит освободился
    -- один из ip и пропал из таблицы занятых ip, выдаём его
    if t_ip_iter < t_ip_lease
    then
      -- raise notice 'current ip is less than ip lease, got it %', t_ip_iter;
      return t_ip_iter;
    end if;

    raise exception 'End loop, unexpected!';
  end loop;

  return null;
END
$$;



--
-- Finds ip_pool by ip addr, where ip belongs to the network
--
CREATE OR REPLACE FUNCTION find_ip_pool_by_ip(
  v_ip inet)
  RETURNS SETOF networks_ip_pool AS
$$
select *
from networks_ip_pool
where
  v_ip <<= network
limit 1
for update skip locked;
$$
LANGUAGE sql;



--
-- Find customer by device mac and device port, if device supports
-- port allocation to customer
--
CREATE OR REPLACE FUNCTION find_customer_by_device_credentials(
  v_dev_mac  macaddr,
  v_dev_port smallint)
  RETURNS SETOF customers AS
$$
-- find customer by device mac and device port
select cs.*
from customers cs
  left join device dv on (dv.id = cs.device_id)
  left join device_port dp on (cs.dev_port_id = dp.id)
  left join device_dev_type_is_use_dev_port ddtiudptiu on (ddtiudptiu.dev_type = dv.dev_type)
where dv.mac_addr = v_dev_mac
      and ((not ddtiudptiu.is_use_dev_port) or dp.num = v_dev_port)
limit 1;
$$
LANGUAGE sql;



--
-- Checks if customer with specified ip has permit to service
--
CREATE OR REPLACE FUNCTION find_service_permit(
  v_ip inet)
  RETURNS SETOF boolean AS
$$

  select exists(select services.id
  from services
    left join customer_service on (customer_service.service_id = services.id)
    left join customers on (customers.current_service_id = customer_service.id)
    left join base_accounts on (base_accounts.id = customers.baseaccount_ptr_id)
    left join networks_ip_leases nil on (nil.customer_id = customers.baseaccount_ptr_id)
  where nil.ip_address = v_ip and base_accounts.is_active
  limit 1);

$$
LANGUAGE sql;
