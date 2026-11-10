
CREATE TABLE IF NOT EXISTS pagamentos (
    id SERIAL PRIMARY KEY,

    pedido_id INTEGER NOT NULL,

    valor NUMERIC(12, 2) NOT NULL,

    metodo VARCHAR(30) NOT NULL,

    status VARCHAR(20) NOT NULL DEFAULT 'pendente',

    referencia_externa VARCHAR(100),

    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_pagamentos_pedidos
        FOREIGN KEY (pedido_id)
        REFERENCES pedidos(id),

    CONSTRAINT chk_pagamentos_valor
        CHECK (valor > 0),

    CONSTRAINT chk_pagamentos_metodo
        CHECK (metodo IN ('pix', 'cartao', 'boleto')),

    CONSTRAINT chk_pagamentos_status
        CHECK (status IN ('pendente', 'aprovado', 'recusado', 'cancelado'))
);

CREATE INDEX IF NOT EXISTS idx_pagamentos_pedido_id
    ON pagamentos (pedido_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_pagamentos_aprovado_unico
    ON pagamentos (pedido_id)
    WHERE status = 'aprovado';

CREATE UNIQUE INDEX IF NOT EXISTS idx_pagamentos_referencia_externa
    ON pagamentos (referencia_externa)
    WHERE referencia_externa IS NOT NULL;
