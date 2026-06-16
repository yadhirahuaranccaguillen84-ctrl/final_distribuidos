-- Corrige get_customer_balance: reemplaza IF() (MySQL) por CASE (PostgreSQL)
-- Ejecutar en Supabase SQL Editor si ya cargaste sakila-supabase.sql

CREATE OR REPLACE FUNCTION get_customer_balance(
    p_customer_id integer,
    p_effective_date timestamp without time zone
) RETURNS numeric
LANGUAGE plpgsql
AS $$
DECLARE
    v_rentfees DECIMAL(5,2);
    v_overfees INTEGER;
    v_payments DECIMAL(5,2);
BEGIN
    SELECT COALESCE(SUM(film.rental_rate), 0) INTO v_rentfees
    FROM film, inventory, rental
    WHERE film.film_id = inventory.film_id
      AND inventory.inventory_id = rental.inventory_id
      AND rental.rental_date <= p_effective_date
      AND rental.customer_id = p_customer_id;

    SELECT COALESCE(SUM(
        CASE
            WHEN rental.return_date IS NOT NULL
              AND (rental.return_date::date - rental.rental_date::date) > film.rental_duration
            THEN (rental.return_date::date - rental.rental_date::date) - film.rental_duration
            ELSE 0
        END
    ), 0) INTO v_overfees
    FROM rental, inventory, film
    WHERE film.film_id = inventory.film_id
      AND inventory.inventory_id = rental.inventory_id
      AND rental.rental_date <= p_effective_date
      AND rental.customer_id = p_customer_id;

    SELECT COALESCE(SUM(payment.amount), 0) INTO v_payments
    FROM payment
    WHERE payment.payment_date <= p_effective_date
      AND payment.customer_id = p_customer_id;

    RETURN v_rentfees + v_overfees - v_payments;
END;
$$;
