BEGIN;

ALTER TABLE clientes
ADD COLUMN IF NOT EXISTS perfil VARCHAR(20);

UPDATE clientes
SET perfil = 'cliente'
WHERE perfil IS NULL;

ALTER TABLE clientes
ALTER COLUMN perfil SET DEFAULT 'cliente';

ALTER TABLE clientes
ALTER COLUMN perfil SET NOT NULL;

ALTER TABLE clientes
DROP CONSTRAINT IF EXISTS clientes_perfil_check;

ALTER TABLE clientes
ADD CONSTRAINT clientes_perfil_check
CHECK (perfil IN ('cliente', 'admin'));

COMMIT;
